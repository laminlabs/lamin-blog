import nox
from laminci import move_built_docs_to_slash_project_slug
from laminci.nox import run_pre_commit

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
def build(session: nox.Session):
    session.run(*"cd ./lndocs && uv pip install --system -e .".split())
    session.run(*["lndocs", "--strict"])
    move_built_docs_to_slash_project_slug()
