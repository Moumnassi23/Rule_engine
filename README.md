# Rule Engine

Le rule engine est un moteur de regles qui sert a stocker, parser et distribuer les regles.
Au lieu de traiter les regles dans des scripts pyspark et cela implique la tracabilite de la regles, on stocke/traite les regles dans un moteur independamment du code.

Le rule engine a 3 composants principaux :

## 1 - La base de regles (RB)

La RB sert a definir les regles dans des fichiers yaml avec un ordre specifique qui repond au besoin metiers et puis ce fichier est stocké donc ça implique le stockage de la regle.

### Structure de fichier yaml

Le fichier yaml doit avoir un minimum strict sinon le fichier est rejeté. Pour cela on cite les elements de base d'un fichier yaml :

1. La version de la regle
2. La description de la regle
3. La date de la regle
4. La date d'execution du code relatif a la regle
5. Le commit-id

Apres avoir cité les elements de base on passe a la structure generale du yaml.

Les regles sont generalement decoupées en 2 types de regles (Direct et Indirect) :

- **Les regles directes** sont par exemple des filtres, des calculs ou meme des aggregations sans jointure.
- **Les regles indirectes** on peut les modeliser comme la regle fondamentale ou la finalite du projet : des jointures entre les tables qui menent a une specification de perimetre.

> **Note importante sur l'ordre des actions**
>
> Meme si les fichiers yaml par leur nature n'ont pas la notion d'ordre, dans notre projet il faut assumer que l'ordre des actions du fichier yaml sera l'ordre de planification.
>
> **Exemple** : si dans le fichier yaml on a un filtre avant la jointure, alors au moment d'execution on filtre puis on applique notre jointure.

---

### Syntaxe standard de fichier yaml

Afin de garantir le meme langage dans toutes les equipes de CDM, on doit specifier une syntaxe a respecter. Tout fichier yaml de regle doit utiliser exactement les cles suivantes :

#### Cles de metadonnees

| Element | Cle yaml | Description |
|---------|----------|-------------|
| La version | `version` | Version de la regle au format semver (ex: `1.0.0`) |
| La description | `description` | Description metier de la regle |
| La date de la regle | `rule_date` | Date de creation ou derniere modification |
| La date d'execution | `exec_date` | Date de reference pour l'execution |
| Le commit-id | `commit_id` | Identifiant du commit Git (injecté automatiquement par la CI) |

#### Cles de structure

| Element | Cle yaml | Description |
|---------|----------|-------------|
| Les inputs | `inputs` | Liste des tables/DataFrames en entree |
| La pipeline | `pipeline` | Bloc qui contient la logique de transformation |
| Les etapes | `steps` | Liste ordonnée des actions a executer |
| Le type d'etape | `type` | Type de l'action (filter, join, aggregate, etc.) |

#### Squelette d'un fichier yaml conforme

```yaml
version: "1.0.0"
description: "Description metier de la regle"
rule_date: "2026-05-14"
exec_date: "${exec_date}"
commit_id: ""   # injecté par la CI

inputs:
  - name: <nom_logique>
    table: <nom_table>

pipeline:
  steps:
    - type: <type_d_etape>
      ...
```

#### Regles de syntaxe a respecter

Pour garantir l'uniformité entre toutes les equipes CDM, les conventions suivantes sont obligatoires :

1. **Toutes les cles sont en `snake_case`** et en minuscules
2. **L'ordre des blocs de metadonnees** doit suivre cet ordre : `version`, `description`, `rule_date`, `exec_date`, `commit_id`, puis `inputs`, puis `pipeline`
3. **Les noms d'inputs et de steps** sont en snake_case, avec un verbe a l'infinitif pour les steps (ex: `filtrer_valides`, `enrichir_avec_etat`)
4. **Les valeurs string** sont entre guillemets doubles, sauf pour les nombres et booleens
5. **L'ordre des steps** dans la liste = l'ordre d'execution (cf. note ci-dessus)
6. **Le `commit_id` ne doit jamais etre renseigné a la main** : il est injecté automatiquement par la CI a chaque push

---

### Ecriture des conditions et expressions

Pour garantir un langage **lisible par tous les profils** (data engineers, analystes metier, auditeurs), les conditions et expressions ne sont pas ecrites en code PySpark dans le yaml. On utilise un DSL declaratif structuré : on decrit **ce qu'on veut**, et le moteur se charge de traduire en PySpark.

#### Principe general

Chaque condition est decrite par trois elements :
- `column` : la colonne concernee
- `operator` : l'operation a appliquer
- `value` ou `values` : la valeur (ou les valeurs) de comparaison

Le moteur traduit automatiquement en PySpark. Par exemple :

```yaml
- column: etat
  operator: "=="
  value: "VALIDE"
```

→ traduit en interne par le moteur en : `col("etat") == "VALIDE"`

#### Liste des operateurs supportés

| Operateur | Description | Champ valeur | Equivalent PySpark |
|-----------|-------------|--------------|--------------------|
| `==` | Egalite | `value` | `col(c) == v` |
| `!=` | Difference | `value` | `col(c) != v` |
| `>` | Superieur strict | `value` | `col(c) > v` |
| `<` | Inferieur strict | `value` | `col(c) < v` |
| `>=` | Superieur ou egal | `value` | `col(c) >= v` |
| `<=` | Inferieur ou egal | `value` | `col(c) <= v` |
| `in` | Appartient a une liste | `values` | `col(c).isin(*vs)` |
| `not_in` | N'appartient pas a une liste | `values` | `~col(c).isin(*vs)` |
| `is_null` | Est NULL | (aucun) | `col(c).isNull()` |
| `is_not_null` | N'est pas NULL | (aucun) | `col(c).isNotNull()` |
| `like` | Correspond a un motif | `value` | `col(c).like(v)` |

#### Conditions simples (une seule condition)

Pour un filtre avec une seule condition, on ecrit directement :

```yaml
- type: filter
  column: etat
  operator: "=="
  value: "VALIDE"
```

→ `df.filter(col("etat") == "VALIDE")`

#### Conditions multiples (plusieurs conditions a combiner)

Quand plusieurs conditions doivent etre combinees, on les place dans une liste `conditions` avec un operateur logique global (`AND` ou `OR`). Pour la concision, on utilise la **syntaxe inline yaml** `{...}` qui place chaque condition sur une ligne :

```yaml
- type: filter
  logical: AND
  conditions:
    - {column: etat, operator: "==", value: "VALIDE"}
    - {column: solde, operator: ">=", value: 1000}
    - {column: date_cloture, operator: is_null}
```

→ `(col("etat") == "VALIDE") & (col("solde") >= 1000) & col("date_cloture").isNull()`

#### Conditions avec des listes de valeurs

Pour les operateurs `in` et `not_in`, on utilise le champ `values` (au pluriel) :

```yaml
- type: filter
  logical: AND
  conditions:
    - {column: type_compte, operator: in, values: [COURANT, EPARGNE, TERME]}
    - {column: devise, operator: not_in, values: [USD, GBP]}
```

#### Conditions imbriquees (mix AND/OR)

Pour les cas complexes ou il faut melanger AND et OR, on utilise l'imbrication avec les blocs `AND` et `OR` :

```yaml
# Exemple : "compte valide ET (type courant OU type epargne) ET pas de date de cloture"
- type: filter
  AND:
    - {column: etat, operator: "==", value: "VALIDE"}
    - OR:
        - {column: type_compte, operator: "==", value: "COURANT"}
        - {column: type_compte, operator: "==", value: "EPARGNE"}
    - {column: date_cloture, operator: is_null}
```

→ `(col("etat") == "VALIDE") & ((col("type_compte") == "COURANT") | (col("type_compte") == "EPARGNE")) & col("date_cloture").isNull()`

Les blocs `AND` et `OR` peuvent etre imbriques sans limite de profondeur, mais on **deconseille de depasser 3 niveaux** pour preserver la lisibilite. Au-dela, il faut decouper en plusieurs steps de filtre.

#### KPI et colonnes calculees

Pour les calculs simples, on utilise le step `kpi` avec une syntaxe operatoire :

```yaml
- type: kpi
  expressions:
    - name: taux_endettement
      operation: divide
      operands: [encours_credit, revenu_mensuel]
      multiply_by: 100
```

→ `col("encours_credit") / col("revenu_mensuel") * 100`

Pour les categorisations conditionnelles, on utilise `case` :

```yaml
- type: kpi
  expressions:
    - name: categorie_risque
      case:
        - when: {column: taux_endettement, operator: ">", value: 33}
          then: "ELEVE"
        - when: {column: taux_endettement, operator: ">", value: 20}
          then: "MOYEN"
        - else: "FAIBLE"
```

→ `when(col("taux_endettement") > 33, "ELEVE").when(col("taux_endettement") > 20, "MOYEN").otherwise("FAIBLE")`

#### Aggregations

Les aggregations specifient la fonction et la colonne en clair :

```yaml
- type: aggregate
  group_by: [tier_id, tier_nom]
  metrics:
    - {name: solde_total, function: sum, column: solde}
    - {name: nb_comptes, function: count_distinct, column: compte_id}
    - {name: solde_moyen, function: avg, column: solde}
    - {name: solde_max, function: max, column: solde}
```

Fonctions d'aggregation supportees : `sum`, `count`, `count_distinct`, `avg`, `min`, `max`.

#### Regles de syntaxe strictes pour les conditions et expressions

Pour garantir l'uniformite entre toutes les equipes CDM :

1. **Une condition simple** (1 seul filtre) peut etre ecrite a plat (`column`, `operator`, `value` directement sous le step). Au-dela d'une condition, utiliser obligatoirement le bloc `conditions` avec un `logical` explicite.
2. **Les operateurs symboles sont entre guillemets** (`"=="`, `">="`, etc.) pour eviter l'interpretation yaml. Les operateurs textuels (`in`, `is_null`, `like`) ne necessitent pas de guillemets.
3. **Utiliser `values` (pluriel)** pour les operateurs `in` et `not_in`, et `value` (singulier) pour les autres operateurs.
4. **Les noms de colonnes ne sont jamais entre guillemets** dans les champs `column`. Les valeurs strings, oui.
5. **L'imbrication AND/OR ne doit pas depasser 3 niveaux**. Au-dela, decouper en plusieurs steps de filtre.
6. **Le champ `logical` est obligatoire** des qu'il y a plus d'une condition dans `conditions`, meme si c'est AND (pour eviter les ambiguites de lecture).

#### Pourquoi ce format declaratif ?

Le yaml decrit la **logique metier**, pas son implementation. Cela permet de :

- **Lisibilite universelle** : un analyste metier, un product owner, un auditeur peut lire et valider une regle sans connaitre PySpark
- **Securite** : aucun code n'est evalue depuis le yaml, donc aucune possibilite d'injection ou d'execution arbitraire
- **Validation stricte** : le parser verifie que chaque condition est bien formee avant l'execution
- **Portabilite** : la meme regle peut etre traduite vers d'autres moteurs (Snowflake, BigQuery) en changeant uniquement la couche de traduction
- **Audit** : les regles s'affichent en clair dans n'importe quel outil de revue (GitLab, GitHub, Confluence)

---

#### Exemple complet

```yaml
version: "1.0.0"
description: "Calcul du solde total par tier pour la date de reference"
rule_date: "2026-05-14"
exec_date: "${exec_date:-current_date()}"
commit_id: ""

inputs:
  - {name: compte, table: silver.compte}
  - {name: code_etat_compte, table: silver.code_etat_compte}
  - {name: mouvement, table: silver.mouvement}
  - {name: tier, table: silver.tier}

pipeline:
  steps:
    - type: join
      with: code_etat_compte
      broadcast: true

    - type: filter
      column: etat
      operator: "=="
      value: "VALIDE"

    - type: join
      with: mouvement

    - type: filter
      column: date_mouvement
      operator: "=="
      value: "${exec_date}"

    - type: join
      with: tier
      broadcast: true

    - type: aggregate
      group_by: [tier_id, tier_nom]
      metrics:
        - {name: solde_total, function: sum, column: solde}
        - {name: nb_comptes, function: count_distinct, column: compte_id}
```

Tout fichier qui ne respecte pas cette syntaxe est rejeté par le parser au moment du chargement, **avant meme le demarrage du job Spark**.