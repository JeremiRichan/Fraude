import random
import math
import sys

# Augmenter la limite de récursion pour Bron-Kerbosch sur grands graphes
sys.setrecursionlimit(10_000)


def calculer_probabilite(n: int) -> float:
    if n <= 1:
        return 0.0
    if n <= 10:
        return 0.60
    if n <= 30:
        return 0.40
    seuil = math.log(n) / n
    if n <= 100:
        return round(min(1.0, 1.5 * seuil), 4)
    if n <= 500:
        return round(min(1.0, 2.0 * seuil), 4)
    return round(min(1.0, 2.5 * seuil), 4)

def generer_graphe(n: int, p: float) -> dict:
    """
    Génère un graphe aléatoire non orienté G(n, p) — modèle Erdős–Rényi.
    Retourne un dict {sommet: set(voisins)}.
    """
    if n < 1:
        raise ValueError(f"n doit être >= 1, reçu : {n}")
    graphe = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if random.random() <= p:
                graphe[i].add(j)
                graphe[j].add(i)
    return graphe

def bfs(graphe: dict, depart: int) -> set:
    """
    Parcours en largeur depuis `depart`.
    Retourne l'ensemble des sommets atteignables.
    """
    visites = {depart}
    file = [depart]
    tete = 0
    while tete < len(file):
        sommet = file[tete]
        tete += 1
        for voisin in graphe[sommet]:
            if voisin not in visites:
                visites.add(voisin)
                file.append(voisin)
    return visites

def composantes_connexes(graphe: dict) -> list:
    """Retourne la liste des composantes connexes (chacune est un set)."""
    non_visites = set(graphe.keys())
    composantes = []
    while non_visites:
        depart = next(iter(non_visites))
        comp = bfs(graphe, depart)
        composantes.append(comp)
        non_visites -= comp
    return composantes


def rendre_connexe(graphe: dict) -> None:
    composantes = composantes_connexes(graphe)
    # Relier chaque composante à la suivante en une seule passe
    while len(composantes) > 1:
        s1 = random.choice(list(composantes[0]))
        s2 = random.choice(list(composantes[1]))
        graphe[s1].add(s2)
        graphe[s2].add(s1)
        composantes = composantes_connexes(graphe)

def colorier(graphe: dict) -> dict:
    ordre = sorted(graphe, key=lambda s: len(graphe[s]), reverse=True)
    couleur: dict = {}
    for sommet in ordre:
        couleurs_voisins = {couleur[v] for v in graphe[sommet] if v in couleur}
        c = 0
        while c in couleurs_voisins:
            c += 1
        couleur[sommet] = c
    return couleur

def bron_kerbosch(graphe: dict, R: set, P: set, X: set, cliques: list) -> None:
    if not P and not X:
        if len(R) >= 3:
            cliques.append(frozenset(R))
        return

    # Choix du pivot : sommet de P ∪ X maximisant |voisins ∩ P|
    pivot = max(P | X, key=lambda u: len(graphe[u] & P))

    for sommet in list(P - graphe[pivot]):
        voisins = graphe[sommet]
        bron_kerbosch(graphe, R | {sommet}, P & voisins, X & voisins, cliques)
        P = P - {sommet}
        X = X | {sommet}


def trouver_cliques(graphe: dict) -> list:
    """Retourne la liste de toutes les cliques maximales de taille >= 3."""
    cliques: list = []
    sommets = set(graphe.keys())
    bron_kerbosch(graphe, set(), sommets, set(), cliques)
    return cliques

def assigner_roles(couleur: dict) -> dict:
    return {s: min(c, 3) for s, c in couleur.items()}


def detecter_fraude(graphe: dict, roles: dict) -> tuple:
    sommets_frauduleux: set = set()
    aretes_frauduleuses: set = set()

    for u in graphe:
        for v in graphe[u]:
            if u < v:
                ru, rv = roles[u], roles[v]
                if (ru == 0 and rv == 2) or (ru == 2 and rv == 0):
                    aretes_frauduleuses.add((u, v))
                    sommets_frauduleux.update([u, v])

    for s, role in roles.items():
        if role == 3:
            sommets_frauduleux.add(s)

    return sommets_frauduleux, aretes_frauduleuses


def compter_roles(roles: dict) -> dict:
    """Retourne le comptage {0: n_conso, 1: n_fourn, 2: n_appro, 3: n_susp}."""
    compteurs = {0: 0, 1: 0, 2: 0, 3: 0}
    for role in roles.values():
        compteurs[min(role, 3)] += 1
    return compteurs


def disposition_aleatoire(
    graphe: dict,
    largeur: float = 2.0,
    hauteur: float = 2.0,
    dist_min: float = 0.08,
    max_tentatives: int = 30,
) -> dict:
    positions: dict = {}
    demi_l = largeur / 2
    demi_h = hauteur / 2

    for sommet in graphe:
        meilleure_pos = None
        meilleure_dist = -1.0

        for _ in range(max_tentatives):
            x = random.uniform(-demi_l, demi_l)
            y = random.uniform(-demi_h, demi_h)

            if not positions:
                meilleure_pos = (x, y)
                break

            # Distance minimale aux sommets déjà placés
            dist_min_loc = min(
                (x - px) ** 2 + (y - py) ** 2
                for px, py in positions.values()
            ) ** 0.5

            if dist_min_loc >= dist_min:
                meilleure_pos = (x, y)
                break

            if dist_min_loc > meilleure_dist:
                meilleure_dist = dist_min_loc
                meilleure_pos = (x, y)

        positions[sommet] = meilleure_pos  # type: ignore[assignment]

    return positions


def construire(n: int) -> dict:
    if n < 2:
        raise ValueError(f"Le graphe nécessite au moins 2 sommets (reçu n={n}).")

    p = calculer_probabilite(n)
    graphe = generer_graphe(n, p)
    rendre_connexe(graphe)

    couleur = colorier(graphe)
    roles = assigner_roles(couleur)

    sommets_frauduleux, aretes_frauduleuses = detecter_fraude(graphe, roles)
    compteurs = compter_roles(roles)
    nb_couleurs = max(couleur.values()) + 1 if couleur else 1

    pos = disposition_aleatoire(graphe)
    cliques = trouver_cliques(graphe)

    # Arêtes et sommets appartenant à au moins une clique
    aretes_cliques: set = set()
    sommets_dans_cliques: set = set()
    for c in cliques:
        sommets_dans_cliques.update(c)
        lst = list(c)
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                aretes_cliques.add((min(lst[i], lst[j]), max(lst[i], lst[j])))

    return {
        'graphe':               graphe,
        'pos':                  pos,
        'couleur':              couleur,
        'roles':                roles,
        'probabilite':          p,
        'nb_couleurs':          nb_couleurs,
        'sommets_frauduleux':   sommets_frauduleux,
        'aretes_frauduleuses':  aretes_frauduleuses,
        'compteurs':            compteurs,
        'nb_sommets':           n,
        'nb_aretes':            sum(len(v) for v in graphe.values()) // 2,
        'cliques':              cliques,
        'aretes_cliques':       aretes_cliques,
        'sommets_dans_cliques': sommets_dans_cliques,
    }
