Ajoute une nouvelle étape.
Cette étape se nomme "Youtube - Sous-titres"
Tu peux t'inspirer de 'YoutubeInfosVideo*' au besoin.

# Fichiers à créer (4 nouveaux fichiers)

1. __src__/models/steps/youtube_subtitles_params.py

Class YoutubeSubtitlesParams(BaseModel) avec les champs :
download_fra_srt: bool (requis)
download_eng_srt: bool (requis)
comment: str = ""

Validator custom nécessaire :
Le commentaire ne doit pas dépasser 50 caractères si alimenté.

2. __src__/services/steps/youtube_subtitles_executor.py

- Class YoutubeSubtitlesExecutor(IStepExecutor)
- step_type() → StepTypeEnum.E_YOUTUBE_SUBTITLES
- execute_logical(browser, context) : cast vers YoutubeSubtitlesParams
- register_step_executor(YoutubeSubtitlesExecutor()) en fin de module

3. __src__/views/steps/youtube_subtitles_form_def.py

Constantes :
- C_KEY_DOWNLOAD_FRA_SRT = "download_fra_srt"
- C_KEY_DOWNLOAD_ENG_SRT = "download_eng_srt"
- C_KEY_COMMENT = "comment"

Class YoutubeSubtitlesFormDef(IStepFormDef)
- build_form : composé de 3 lignes : 2 cases à cocher + un commentaire via ttk.Entry
- load_params_step_to_widget / read_params_from_view pour les champs
- register_form(YoutubeSubtitlesFormDef()) en fin de module

4. __src__/presenters/steps/youtube_subtitles_presenter.py

- Fonction _build(data) → YoutubeSubtitlesParams(...)
- register_params_builder(StepTypeEnum.E_YOUTUBE_SUBTITLES, _build)

# Fichiers à modifier (7 fichiers)

Fichier	Modification
__src__/shared/enums.py ligne       Ajouter E_YOUTUBE_SUBTITLES = "YOUTUBE_SUBTITLES" dans StepTypeEnum
__src__/models/steps/__init__.py	Import YoutubeSubtitlesParams + ajout dans __all__
__src__/services/steps/__init__.py	Import YoutubeSubtitlesExecutor + ajout dans __all__
__src__/views/steps/__init__.py	    Import YoutubeSubtitlesFormDef + ajout dans __all__
__src__/presenters/steps/__init__.py	Import _build as _b_YOUTUBE_SUBTITLES # noqa: F401
__src__/presenters/step_label_formatters.py	Ajouter _fmt_youtube_subtitles(params, _idx, _ctx) → f"Télécharger '.srt'\nFRA : {oui/non}  |  ENG : {oui/non}" et l'entrée dans le registry
__src__/shared/i18n_fra.py	C_STEP_TYPE_TO_LABELS : ajouter StepTypeEnum.E_YOUTUBE_SUBTITLES: "Télécharger '.srt'"

Comportements spécifiques à YOUTUBE_SUBTITLES
- Erreur possible : Si les 2 champs ont leurs variable 'bool' à False. Au moins 1 des 2 champs bool doit être à True.
- La signature execute_logical(browser, context) reste identique (imposée par l'interface).
- Log attendu : utiliser le même mécanisme de logging que les autres executors.

main.py : rien à toucher — le bootstrap importe déjà les packages entiers via import models.steps, import services.steps, etc.
