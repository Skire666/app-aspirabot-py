Ajoute une nouvelle étape.
Cette étape se nomme "Recommencer au début"
Tu peux t'inspirer de 'CheckUrlPage*' au besoin.

# Fichiers à créer (4 nouveaux fichiers)

1. __src__/models/steps/restart_to_beginning_params.py

Class RestartToBeginningParams(BaseModel) avec les champs :
jump_only_if_urls_remaining: bool (requis)
comment: str = ""

Validator custom nécessaire :
Le commentaire ne doit pas dépasser 50 caractères si alimenté.

2. __src__/services/steps/restart_to_beginning_executor.py

- Class RestartToBeginningExecutor(IStepExecutor)
- step_type() → StepTypeEnum.E_CHECK_URL_PAGE
- execute_logical(browser, context) : cast vers RestartToBeginningParams
- register_step_executor(SectionExecutor()) en fin de module

3. __src__/views/steps/restart_to_beginning_form_def.py

Constantes :
- C_JUMP_ONLY_IF_URLS_REMAINING= "jump_only_if_urls_remaining"
- C_KEY_COMMENT = "comment"

Class RestartToBeginningFormDef(IStepFormDef)
- build_form : 3 lignes : 2 cases à cocher, et un commentaire via ttk.Entry
- load_params_step_to_widget / read_params_from_view sur les champs
- register_form(SectionFormDef()) en fin de module

4. __src__/presenters/steps/restart_to_beginning_step_presenter.py

- Fonction _build(data) → RestartToBeginningParams(...)
- register_params_builder(StepTypeEnum.E_CHECK_URL_PAGE, _build)

# Fichiers à modifier (7 fichiers)

Fichier	Modification
__src__/shared/enums.py ligne       Ajouter E_RESTART_TO_BEGINNING = "RESTART_TO_BEGINNING" dans StepTypeEnum
__src__/models/steps/__init__.py	Import RestartToBeginningParams + ajout dans __all__
__src__/services/steps/__init__.py	Import RestartToBeginningExecutor + ajout dans __all__
__src__/views/steps/__init__.py	    Import RestartToBeginningFormDef + ajout dans __all__
__src__/presenters/steps/__init__.py	Import _build as _b_restart_to_beginning # noqa: F401
__src__/presenters/step_label_formatters.py	Ajouter _fmt_restart_to_beginning(params, _idx, _ctx) → f"Vérifier la page\nDomaine : {oui/non}  |  Chemin : {oui/non}" + entrée dans _REGISTRY
__src__/shared/i18n_fra.py	C_STEP_TYPE_TO_LABELS : ajouter StepTypeEnum.E_CHECK_URL_PAGE: "Vérifier URL de la page"

Comportements spécifiques à RESTART_TO_BEGINNING
- Erreur possible : Si les 2 champs ont leurs variable 'bool' à False. Au moins 1 des 2 champs bool doit être à True.
- Browser : Récupère la page 'get_workflow_page' et regarde l'URL. Compare avec la dernière URL utilisée 'last_url_opened'.
- La signature execute_logical(browser, context) reste identique (imposée par l'interface).
- Log attendu : utiliser le même mécanisme de logging que les autres executors.

main.py : rien à toucher — le bootstrap importe déjà les packages entiers via import models.steps, import services.steps, etc.
