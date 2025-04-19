# CLI

Ce projet utilise [Typer](https://typer.tiangolo.com/) et [Click](https://click.palletsprojects.com/) pour la CLI. Quand le projet est installé, la commande `tvdata` est disponible.

L'aide complète est accessible avec :

```bash
tvdata --help
```

La CLI est définie dans `tvdata.cli`. De nouvelles commandes peuvent être ajoutées ici.

## Exemples

Des exemples d'utilisation sont disponibles dans le dossier `examples/` à la racine du projet.

## Typage

Toutes les fonctions publiques sont typées pour la compatibilité avec mypy.
