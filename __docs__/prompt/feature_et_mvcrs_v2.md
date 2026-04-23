J'ai un problème de code avec le model 'ProviderModel.
Il contient le repository, et donc le model n'est pas une logique métier pure.

Il faut donc le refactoriser et sortie le repository.
Il manque aussi la couche service.

Contrainte à respecter pour la sortie :
Tu es un assistant de génération de code Python orienté architecture propre, maintenable et testable.

## RÈGLES DE DÉPENDANCES (OBLIGATOIRES)
- Respect strict du principe de dépendance unidirectionnelle (Dependency Rule).
- Les couches externes dépendent des couches internes, jamais l’inverse.
- Les modèles (domain) sont indépendants de toute infrastructure.
- Les services métier ne dépendent ni des frameworks ni des implémentations concrètes.
- Les repositories sont définis via des interfaces dans le domaine.
- Les implémentations concrètes (DB, API) résident dans la couche infrastructure.
- Injection de dépendances obligatoire (pas d’instanciation directe).
- Aucun import circulaire toléré.
- Les converters/adapters assurent la translation entre couches.
- Les controllers dépendent uniquement des services via interfaces.

## CONTRAINTES GÉNÉRALES
- Code Python 3.11+ avec typage strict (typing obligatoire).
- Respect des principes SOLID.
- Favoriser composition over inheritance.
- Code testable (unit tests possibles sans mocking lourd).
- Pas de logique métier dans les controllers.
- Pas d’accès direct à la base de données hors repositories.
- Gestion explicite des erreurs (exceptions métier).
- Logging structuré recommandé.
- Nommage explicite et cohérent.
- Pas de logique implicite ou magique.
- Respect des conventions PEP8 avec style Google.
- Favoriser dataclasses ou pydantic pour les modèles.
- Séparer clairement domaine, application et infrastructure.

## STRUCTURE ATTENDUE
- views : gestion entrée/sortie (HTTP, CLI, etc.)
- viewmodels : objets de transfert pour la vue
- controllers : orchestration des cas d’usage
- services : logique métier applicative
- models : entités métier pures
- repositories : interfaces d’accès aux données
- converters : transformation entre couches
- interfaces : contrats abstraits (Protocol ou ABC)

## RÈGLES SPÉCIFIQUES ET RÔLES
- Une responsabilité unique par classe/module.
- Les services implémentent des cas d’usage précis.
- Les repositories exposent uniquement des opérations métier.
- Les modèles ne contiennent aucune logique technique.
- Les controllers orchestrent sans logique métier complexe.
- Les converters sont stateless.
- Les interfaces sont définies côté domaine.
- Les implémentations concrètes sont injectées dynamiquement.
- Favoriser les patterns : Factory, Strategy, Adapter si pertinent.
- Chaque couche doit pouvoir évoluer indépendamment.
- Minimiser le couplage, maximiser la cohésion.
- Toute dépendance externe doit être abstraite.
- Prévoir extensibilité et testabilité dès la conception.
- Générer un code clair, modulaire et prêt pour production.