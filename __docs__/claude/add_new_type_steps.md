Plan d'implémentation — Step Section
Spécificité de Section vs ScrollDown
Section n'interagit pas avec le browser : son execute_logical ne prend pas browser, logue simplement le titre, et retourne succès. C'est le cas d'étape le plus simple possible.

Fichiers à créer (4 nouveaux fichiers)
1. __src__/models/steps/section_params.py

Classe SectionParams(BaseStepParams) avec 2 champs :
title: str (requis)
comment: str = ""
Pas de validator custom nécessaire (pas de contrainte numérique)
2. __src__/services/steps/section_executor.py

Classe SectionExecutor(StepExecutorBase, IStepExecutor)
step_type() → StepTypeEnum.E_SECTION_STEPS
execute_logical(browser, context) : cast vers SectionParams, logue le titre, ne lève aucune exception
register_step_executor(SectionExecutor()) en fin de module
3. __src__/views/steps/section_form_def.py

Constantes C_KEY_TITLE = "title", C_KEY_COMMENT = "comment"
Classe SectionFormDef(IStepFormDef)
build_form : 2 sous-formulaires (titre via ttk.Entry, commentaire via ttk.Entry)
load_params_step_to_widget / read_params_from_view sur les 2 champs
register_form(SectionFormDef()) en fin de module
4. __src__/presenters/steps/section_step_presenter.py

Fonction _build(data) → SectionParams(title=data.get("title", ""), comment=data.get("comment", ""))
register_params_builder(StepTypeEnum.E_SECTION_STEPS, _build)
Fichiers à modifier (7 fichiers existants)
Fichier	Modification
__src__/shared/enums.py ligne ~51	Ajouter E_SECTION_STEPS = "SECTION_STEPS" dans StepTypeEnum
__src__/models/steps/__init__.py	Import SectionParams + ajout dans __all__
__src__/services/steps/__init__.py	Import SectionExecutor + ajout dans __all__
__src__/views/steps/__init__.py	Import SectionFormDef + ajout dans __all__
__src__/presenters/steps/__init__.py	Import _build as _b_section # noqa: F401
__src__/presenters/step_label_formatters.py	Ajouter _fmt_section(params, _idx, _ctx) → f"Section\n{params.get('title', '')}" + entrée dans _REGISTRY
__src__/shared/i18n_fra.py	C_STEP_TYPE_TO_LABELS : ajouter StepTypeEnum.E_SECTION_STEPS: "Section"
Points d'attention spécifiques à Section
Pas d'erreur possible : execute_logical ne peut pas échouer → pas de message d'erreur à ajouter dans i18n_fra.py
Browser inutilisé : la signature execute_logical(browser, context) reste identique (imposée par l'interface), mais browser n'est pas appelé
Log attendu : utiliser le même mécanisme de logging que les autres executors (probablement context.log(...) ou logger du module) — à vérifier dans StepExecutorBase
main.py : rien à toucher — le bootstrap importe déjà les packages entiers via import models.steps, import services.steps, etc.