# Suika Game

Implémentation du **Suika Game** (jeu de la pastèque) en Python avec pyglet et pymunk.

## Installation

1. Cloner le repository:
```bash
git clone <repository-url>
cd suika
```

2. Créer et activer l'environnement virtuel:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Installer le package en mode développement:
```bash
pip install -e .
```

## Utilisation

### Script shell
```bash
./run_suika.sh
```

### Ligne de commande
```bash
suika
```

### Python
```python
from suika_game import main
main()
```

## Contrôles

- **Clic gauche**: Lâcher un fruit
- **Clic droit**: Exploser un fruit (debug)
- **A**: Mode autoplay
- **P**: Pause
- **Espace**: Secousse manuelle
- **S**: Secousse automatique
- **M**: Déplacement manuel des fruits
- **T**: Mode machine à laver
- **R**: Redémarrer
- **ESC**: Quitter

## Structure

```
src/suika_game/
├── core/           # Constantes et utilitaires
├── graphics/       # Sprites et rendu
├── physics/        # Simulation physique
├── ui/             # Interface utilisateur
└── assets/         # Images et ressources
```

## Dépendances

- Python 3.11+
- pyglet 2.1.8
- pymunk 7.1.0