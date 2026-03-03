# 🚀 Déploiement sur GitHub - Guide Complet

## Étape 1: Créer le Dépôt GitHub

### Option A: Via l'interface web GitHub
1. Allez sur https://github.com
2. Cliquez sur **"New repository"** (vert en haut à droite)
3. Nom du dépôt: `inf349-projet-session`
4. Description: `INF349 - Projet de Session Flask E-commerce API`
5. Choisissez **Public** (pour la remise) ou **Private**
6. **NE PAS** cocher "Add a README file" (vous en avez déjà un)
7. **NE PAS** cocher "Add .gitignore" (vous en avez déjà un)
8. Cliquez sur **"Create repository"**

### Option B: Via GitHub CLI (si installé)
```bash
gh repo create inf349-projet-session --public --description "INF349 - Projet de Session Flask E-commerce API"
```

## Étape 2: Connecter votre local au distant

### Remplacer `VOTRE_USERNAME` par votre nom d'utilisateur GitHub

```bash
# Ajouter le dépôt distant
git remote add origin https://github.com/VOTRE_USERNAME/inf349-projet-session.git

# Vérifier la connexion
git remote -v
```

## Étape 3: Pousser le code sur GitHub

```bash
# Pousser la branche main
git push -u origin main
```

## Étape 4: Vérifier le déploiement

1. Allez sur votre dépôt GitHub
2. Vous devriez voir tous vos fichiers
3. Vérifiez que le README.md s'affiche correctement

## 🎯 Commandes Complètes (Copy-Paste)

```bash
# 1. Créer le dépôt sur GitHub (manuellement via le site web)

# 2. Connecter au distant (remplacez VOTRE_USERNAME)
git remote add origin https://github.com/VOTRE_USERNAME/inf349-projet-session.git

# 3. Pousser le code
git push -u origin main
```

## 🔧 Si vous avez des problèmes

### Problème: "remote origin already exists"
```bash
# Supprimer l'ancien remote
git remote remove origin

# Ajouter le nouveau
git remote add origin https://github.com/VOTRE_USERNAME/inf349-projet-session.git
```

### Problème: Authentication
```bash
# Configurer Git avec vos informations
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"

# Ou utiliser GitHub Personal Access Token
# Settings > Developer settings > Personal access tokens
```

### Problème: Main vs Master
```bash
# Renommer la branche si nécessaire
git branch -M main
```

## 📝 Vérification Finale

Après le push, votre dépôt GitHub devrait contenir:

### 📁 Structure des fichiers
- `inf349/` (dossier principal de l'application)
- `README.md` (documentation principale)
- `requirements.txt` (dépendances)
- `start_app.py` (lanceur d'application)
- `run_tests.py` (tests)
- `ARCHITECTURE.md` (documentation technique)
- `DEMO.md` (scénarios de démonstration)
- `.gitignore` (fichiers ignorés)

### 🎯 Points clés à vérifier sur GitHub
- ✅ Le README.md s'affiche correctement sur la page du dépôt
- ✅ Tous les fichiers Python sont présents
- ✅ La documentation est visible et formatée
- ✅ Le dépôt est public (pour la remise)

## 🚀 Pour la remise

Une fois sur GitHub, vous pouvez:

1. **Partager le lien** du dépôt avec votre enseignant
2. **Cloner sur une autre machine** pour tester:
   ```bash
   git clone https://github.com/VOTRE_USERNAME/inf349-projet-session.git
   cd inf349-projet-session
   pip install -r requirements.txt
   python start_app.py
   ```

3. **Faire des mises à jour** si nécessaire:
   ```bash
   git add .
   git commit -m "Description des changements"
   git push
   ```

## 🎓 Lien pour la remise

Le lien à partager sera:
```
https://github.com/VOTRE_USERNAME/inf349-projet-session
```

---

**🎯 Votre projet INF349 est maintenant sur GitHub et prêt pour la remise!**
