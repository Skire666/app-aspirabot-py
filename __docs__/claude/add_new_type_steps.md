Ajoute une nouvelle étape.
Cette étape se nomme "Vérifier URL de la page"
Inspire toi de ce que fait 'E_OPEN_URL'

# Fichiers à créer (4 nouveaux fichiers)

1. __src__/models/steps/check_url_page_params.py

Class CheckUrlPageParams(BaseStepParams) avec les champs :
check_domain: bool (requis)
check_path: bool (requis)
comment: str = ""

validator custom nécessaire :
Vérifier si les 2 bool sont à False.
Au moins 1 des 2 bool doit être à True.

2. __src__/services/steps/check_url_page_executor.py

- Class CheckUrlPageExecutor(IStepExecutor)
- step_type() → StepTypeEnum.E_CHECK_URL_PAGE
- execute_logical(browser, context) : cast vers CheckUrlPageParams
- register_step_executor(SectionExecutor()) en fin de module

3. __src__/views/steps/check_url_page_form_def.py

Constantes :
- C_CHECK_DOMAIN = "check_domain"
- C_CHECK_PATH = "check_path"
- C_KEY_COMMENT = "comment"

Class CheckUrlPageFormDef(IStepFormDef)
- build_form : 3 lignes : 2 cases à cocher, et un commentaire via ttk.Entry
- load_params_step_to_widget / read_params_from_view sur les champs
- register_form(SectionFormDef()) en fin de module

4. __src__/presenters/steps/check_url_page_step_presenter.py

- Fonction _build(data) → CheckUrlPageParams(...)
- register_params_builder(StepTypeEnum.E_CHECK_URL_PAGE, _build)

# Fichiers à modifier (7 fichiers)

Fichier	Modification
__src__/shared/enums.py ligne       Ajouter E_CHECK_URL_PAGE = "CHECK_URL_PAGE" dans StepTypeEnum
__src__/models/steps/__init__.py	Import CheckUrlPageParams + ajout dans __all__
__src__/services/steps/__init__.py	Import CheckUrlPageExecutor + ajout dans __all__
__src__/views/steps/__init__.py	    Import CheckUrlPageFormDef + ajout dans __all__
__src__/presenters/steps/__init__.py	Import _build as _b_check_url_page # noqa: F401
__src__/presenters/step_label_formatters.py	Ajouter _fmt_check_url_page(params, _idx, _ctx) → f"Vérifier la page\nDomaine : {oui/non}  |  Chemin : {oui/non}" + entrée dans _REGISTRY
__src__/shared/i18n_fra.py	C_STEP_TYPE_TO_LABELS : ajouter StepTypeEnum.E_CHECK_URL_PAGE: "Vérifier URL de la page"

Comportements spécifiques à CHECK_URL_PAGE
- Erreur possible : Si les 2 champs ont leurs variable 'bool' à False. Au moins 1 des 2 champs bool doit être à True.
- Browser : Récupère la page 'get_workflow_page' et regarde l'URL. Compare avec la dernière URL utilisée 'last_url_opened'.
- La signature execute_logical(browser, context) reste identique (imposée par l'interface).
- Log attendu : utiliser le même mécanisme de logging que les autres executors.

main.py : rien à toucher — le bootstrap importe déjà les packages entiers via import models.steps, import services.steps, etc.
