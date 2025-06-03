
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import bcrypt

USUARIOS_PATH = "usuarios.csv"
LOG_PATH = "log_acessos.csv"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# === Criptografia ===
def hash_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha_digitada, senha_hash):
    return bcrypt.checkpw(senha_digitada.encode(), senha_hash.encode())

# === Usuários ===
def carregar_usuarios():
    if not os.path.exists(USUARIOS_PATH):
        senha_hash = hash_senha("Jacare@92")
        df_init = pd.DataFrame([{"usuario": "Jonathan", "senha": senha_hash}])
        df_init.to_csv(USUARIOS_PATH, index=False)
    return pd.read_csv(USUARIOS_PATH)

def salvar_usuario(novo_usuario, nova_senha):
    df_usuarios = carregar_usuarios()
    if novo_usuario in df_usuarios["usuario"].values:
        return False
    senha_hash = hash_senha(nova_senha)
    df_novo = pd.DataFrame([{"usuario": novo_usuario, "senha": senha_hash}])
    df_usuarios = pd.concat([df_usuarios, df_novo], ignore_index=True)
    df_usuarios.to_csv(USUARIOS_PATH, index=False)
    return True

def excluir_usuario(usuario_para_excluir):
    df_usuarios = carregar_usuarios()
    if usuario_para_excluir == "Jonathan":
        return False
    df_usuarios = df_usuarios[df_usuarios["usuario"] != usuario_para_excluir]
    df_usuarios.to_csv(USUARIOS_PATH, index=False)
    return True

def autenticar(usuario, senha):
    df_usuarios = carregar_usuarios()
    linha = df_usuarios[df_usuarios["usuario"] == usuario]
    if not linha.empty:
        senha_hash = linha.iloc[0]["senha"]
        return verificar_senha(senha, senha_hash)
    return False

def registrar_acesso(usuario):
    datahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([{"usuario": usuario, "datahora": datahora}])
    if os.path.exists(LOG_PATH):
        df_existente = pd.read_csv(LOG_PATH)
        df = pd.concat([df_existente, df], ignore_index=True)
    df.to_csv(LOG_PATH, index=False)

# === Login ===
if not st.session_state.autenticado:
    st.set_page_config(page_title="Login", layout="centered")
    st.title("🔐 Login")

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            if autenticar(usuario, senha):
                st.session_state.autenticado = True
                st.session_state.usuario = usuario
                registrar_acesso(usuario)
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")

else:
    st.set_page_config(page_title="Buscar Endereço", layout="centered")
    st.title("🔍 Buscar Endereço")

    if st.session_state.usuario == "Jonathan":
        st.sidebar.title("⚙️ Painel Administrativo")

        with st.sidebar.expander("➕ Cadastrar novo usuário"):
            novo_usuario = st.text_input("Novo usuário")
            nova_senha = st.text_input("Nova senha", type="password")
            if st.button("Criar usuário", key="criar_usuario"):
                if novo_usuario.strip() == "" or nova_senha.strip() == "":
                    st.warning("Preencha os dois campos.")
                elif salvar_usuario(novo_usuario.strip(), nova_senha.strip()):
                    st.success(f"Usuário '{novo_usuario}' criado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário já existe.")

        with st.sidebar.expander("🗑️ Excluir usuário"):
            df_usuarios = carregar_usuarios()
            usuarios_removiveis = [u for u in df_usuarios["usuario"] if u != "Jonathan"]
            if usuarios_removiveis:
                usuario_excluir = st.selectbox("Selecione o usuário para excluir", usuarios_removiveis)
                if st.button("Excluir usuário", key="excluir_usuario"):
                    if excluir_usuario(usuario_excluir):
                        st.success(f"Usuário '{usuario_excluir}' excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao excluir usuário.")

        with st.sidebar.expander("📜 Ver log de acessos"):
            if os.path.exists(LOG_PATH):
                log = pd.read_csv(LOG_PATH)
                st.dataframe(log.sort_values("datahora", ascending=False), use_container_width=True)
            else:
                st.info("Nenhum acesso registrado ainda.")

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", key="logout"):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.rerun()

    excel_path = "ENDEREÇO CTOP FINAL Atualizado.xlsx"
    if not os.path.exists(excel_path):
        st.error(f"Arquivo '{excel_path}' não encontrado no diretório.")
        st.stop()

    @st.cache_data
    def carregar_dados():
        return pd.read_excel(excel_path)

    df = carregar_dados()

    cidade_escolhida = st.selectbox("Selecione a cidade:", sorted(df["CIDADE"].dropna().unique()))
    df_filtrado = df[df["CIDADE"] == cidade_escolhida]

    ats_disponiveis = df_filtrado["AT"].dropna().unique()
    if len(ats_disponiveis) > 0:
        at_escolhida = st.selectbox("Filtrar por AT:", ["Todas"] + sorted(ats_disponiveis.tolist()))
        if at_escolhida != "Todas":
            df_filtrado = df_filtrado[df_filtrado["AT"] == at_escolhida]

    fac_unicas = df_filtrado["FAC"].dropna().unique()
    if len(fac_unicas) > 0:
        fac_escolhida = st.selectbox("Filtrar por FAC:", ["Todas"] + sorted(fac_unicas.tolist()))
        if fac_escolhida != "Todas":
            df_filtrado = df_filtrado[df_filtrado["FAC"] == fac_escolhida]

    if not df_filtrado.empty:
        st.markdown(f"### ✅ Resultados encontrados: {len(df_filtrado)}")
        colunas_exibidas = ["ID", "Endereço", "BAIRRO", "CIDADE", "AT", "CTO", "FAC"]
        colunas_disponiveis = [col for col in colunas_exibidas if col in df_filtrado.columns]
        st.dataframe(df_filtrado[colunas_disponiveis].reset_index(drop=True), use_container_width=True)
    else:
        st.warning("Nenhum resultado encontrado para os filtros aplicados.")
