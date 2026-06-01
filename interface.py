import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import fraude as F

# --- Palette de couleurs (Thème Sombre) ---
COULEUR_FOND = '#0d1117'
COULEUR_PANNEAU = '#161b22'
COULEUR_CARTE = '#1c2128'
COULEUR_BORDURE = '#30363d'
COULEUR_TEXTE = '#e6edf3'
COULEUR_MUTED = '#7d8590'
COULEUR_ACCENT = '#2188ff'
COULEUR_DANGER = '#f85149'

# Configuration des rôles
CONFIG_ROLES = {
    0: {'nom': 'Consommateur',    'couleur': '#ff6b6b', 'char': 'C'},
    1: {'nom': 'Fournisseur',     'couleur': '#4dabf7', 'char': 'F'},
    2: {'nom': 'Approvisionneur', 'couleur': '#51cf66', 'char': 'A'},
    3: {'nom': 'Suspect',         'couleur': '#fcc419', 'char': 'S'},
}

class Application:
    N_DEF = 30
    N_MAX = 500
    PLACEHOLDER = "Taille n du graphe"

    def __init__(self, racine: tk.Tk):
        self.racine = racine
        racine.title("Detection de Fraude - Analyse des Cliques")
        racine.configure(bg=COULEUR_FOND)
        racine.geometry("1280x760")
        racine.minsize(1000, 650)
        racine.protocol("WM_DELETE_WINDOW", self._fermer)

        # État de l'application
        self.donnees = None
        self.sommet_selectionne = None
        self.occupe = False

        self._construire_ui()
        self._afficher_accueil()

    def _construire_ui(self):
        # Barre latérale gauche
        self.barre = tk.Frame(self.racine, bg=COULEUR_PANNEAU, width=280)
        self.barre.pack(side=tk.LEFT, fill=tk.Y)
        self.barre.pack_propagate(False)
        
        # Séparateur vertical
        tk.Frame(self.racine, bg=COULEUR_BORDURE, width=1).pack(side=tk.LEFT, fill=tk.Y)
        
        # Zone principale
        principale = tk.Frame(self.racine, bg=COULEUR_FOND)
        principale.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._barre_gauche()
        self._zone_principale(principale)

    def _barre_gauche(self):
        b = self.barre
        padding = 14
        
        self._vide(b, 18)
        
        # Titre
        tk.Label(b, text="Analyse des Cliques", font=('Courier New', 12, 'bold'),
                 bg=COULEUR_PANNEAU, fg=COULEUR_TEXTE, anchor='w').pack(padx=padding, fill=tk.X)
        tk.Label(b, text="Visualisation des structures fortes",
                 font=('Courier New', 8), bg=COULEUR_PANNEAU, fg=COULEUR_MUTED, anchor='w').pack(padx=padding, fill=tk.X)
        self._separateur(b, padding)

        # Paramètres
        self._titre_section(b, "PARAMETRES")
        cadre_saisie = tk.Frame(b, bg=COULEUR_CARTE, highlightthickness=1,
                                highlightbackground=COULEUR_BORDURE, highlightcolor=COULEUR_ACCENT)
        cadre_saisie.pack(padx=padding-2, fill=tk.X, pady=(0, 6))
        
        self.var_n = tk.StringVar()
        self.champ_n = tk.Entry(cadre_saisie, textvariable=self.var_n,
                                font=('Courier New', 11), bg=COULEUR_CARTE, fg=COULEUR_MUTED,
                                insertbackground=COULEUR_TEXTE, relief='flat', bd=8)
        self.champ_n.pack(fill=tk.BOTH, expand=True)
        self.champ_n.insert(0, self.PLACEHOLDER)
        self.champ_n.bind('<FocusIn>', lambda e: self._ph_entree())
        self.champ_n.bind('<FocusOut>', lambda e: self._ph_sortie())
        self.champ_n.bind('<Return>', lambda e: self.generer())
        self.champ_n.bind('<KeyRelease>', lambda e: self._maj_badge_p())

        # Badge probabilité
        cadre_badge = tk.Frame(b, bg=COULEUR_PANNEAU)
        cadre_badge.pack(padx=padding-2, fill=tk.X, pady=(0, 8))
        tk.Label(cadre_badge, text="p(n) = ", font=('Courier New', 9),
                 bg=COULEUR_PANNEAU, fg=COULEUR_MUTED).pack(side=tk.LEFT)
        self.var_p_affiche = tk.StringVar(value="auto")
        tk.Label(cadre_badge, textvariable=self.var_p_affiche,
                 font=('Courier New', 10, 'bold'), bg=COULEUR_PANNEAU, fg=COULEUR_ACCENT).pack(side=tk.LEFT, padx=6)
        self.lbl_formule_p = tk.Label(cadre_badge, text="", font=('Courier New', 7),
                                      bg=COULEUR_PANNEAU, fg=COULEUR_MUTED)
        self.lbl_formule_p.pack(side=tk.LEFT)

        self.btn_gen = self._bouton(b, "Generer le graphe", COULEUR_ACCENT, '#1a6de0', self.generer, padding)
        self._separateur(b, padding)

        # Analyse
        self._titre_section(b, "ANALYSE")
        self.btn_cliques = self._bouton(b, "Lister les Cliques", COULEUR_CARTE, '#252c38',
                                        self.afficher_cliques, padding, etat='disabled')
        self._separateur(b, padding)

        # Statistiques
        self._titre_section(b, "STATISTIQUES")
        grille = tk.Frame(b, bg=COULEUR_PANNEAU)
        grille.pack(padx=padding-2, fill=tk.X)
        
        self.sv = {}
        etiquettes = [('n', 'Noeuds'), ('a', 'Arete'), ('c', 'Couleurs'), ('s', 'Suspects')]
        idx = 0
        for cle, lbl in etiquettes:
            carte = tk.Frame(grille, bg=COULEUR_CARTE, padx=4, pady=6)
            carte.grid(row=idx//2, column=idx%2, padx=2, pady=2, sticky='nsew')
            grille.columnconfigure(idx%2, weight=1)
            
            self.sv[cle] = tk.StringVar(value='-')
            couleur_val = '#fcc419' if cle == 's' else COULEUR_TEXTE
            tk.Label(carte, textvariable=self.sv[cle],
                     font=('Courier New', 15, 'bold'), bg=COULEUR_CARTE, fg=couleur_val).pack()
            tk.Label(carte, text=lbl, font=('Courier New', 8), bg=COULEUR_CARTE, fg=COULEUR_MUTED).pack()
            idx += 1
            
        self._separateur(b, padding)

        # Distribution
        self._titre_section(b, "DISTRIBUTION")
        self.dist_vars = {}
        for role, cfg in CONFIG_ROLES.items():
            ligne = tk.Frame(b, bg=COULEUR_PANNEAU)
            ligne.pack(padx=padding, fill=tk.X, pady=2)
            
            tk.Label(ligne, text=cfg['char'], font=('Courier New', 14),
                     bg=COULEUR_PANNEAU, fg=cfg['couleur'], width=2).pack(side=tk.LEFT)
            
            col = tk.Frame(ligne, bg=COULEUR_PANNEAU)
            col.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
            
            v = tk.StringVar(value='0')
            tk.Label(col, textvariable=v, font=('Courier New', 8),
                     bg=COULEUR_PANNEAU, fg=cfg['couleur']).pack(anchor='w')
            tk.Label(col, text=cfg['nom'], font=('Courier New', 7),
                     bg=COULEUR_PANNEAU, fg=COULEUR_MUTED).pack(anchor='w')
            self.dist_vars[role] = v

    def _zone_principale(self, parent):
        # Barre de statut
        bas = tk.Frame(parent, bg=COULEUR_PANNEAU, height=28)
        bas.pack(fill=tk.X, side=tk.BOTTOM)
        bas.pack_propagate(False)
        
        self.var_statut = tk.StringVar(value="Entrez n et cliquez sur Generer")
        tk.Label(bas, textvariable=self.var_statut, font=('Courier New', 9),
                 bg=COULEUR_PANNEAU, fg=COULEUR_MUTED).pack(side=tk.LEFT, padx=12, pady=5)

        # Canvas Matplotlib
        self.fig = plt.Figure(facecolor=COULEUR_FOND)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_fig.get_tk_widget().configure(bg=COULEUR_FOND, highlightthickness=0)
        self.canvas_fig.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_fig.mpl_connect('button_press_event', self._clic_graphe)

    # --- Utilitaires UI ---

    def _vide(self, w, h):
        tk.Frame(w, bg=w.cget('bg'), height=h).pack()

    def _separateur(self, w, p):
        tk.Frame(w, bg=COULEUR_BORDURE, height=1).pack(fill=tk.X, padx=p, pady=8)

    def _titre_section(self, w, t):
        tk.Label(w, text=t, font=('Courier New', 7, 'bold'),
                 bg=COULEUR_PANNEAU, fg=COULEUR_MUTED, anchor='w').pack(padx=14, fill=tk.X, pady=(0, 4))

    def _bouton(self, parent, texte, bg_n, bg_h, cmd, pad, etat='normal'):
        btn = tk.Button(parent, text=texte, font=('Courier New', 9, 'bold'),
                        bg=bg_n, fg=COULEUR_TEXTE, relief='flat', bd=0, pady=8,
                        cursor='hand2', state=etat, command=cmd)
        btn.pack(padx=pad-2, fill=tk.X, pady=(0, 4))
        btn.bind('<Enter>', lambda e: btn.config(bg=bg_h) if str(btn['state']) != 'disabled' else None)
        btn.bind('<Leave>', lambda e: btn.config(bg=bg_n) if str(btn['state']) != 'disabled' else None)
        return btn

    def _ph_entree(self):
        if self.champ_n.get() == self.PLACEHOLDER:
            self.champ_n.delete(0, tk.END)
            self.champ_n.config(fg=COULEUR_TEXTE)

    def _ph_sortie(self):
        if not self.champ_n.get():
            self.champ_n.insert(0, self.PLACEHOLDER)
            self.champ_n.config(fg=COULEUR_MUTED)

    def _maj_badge_p(self):
        try:
            n_val = int(self.champ_n.get())
            n_val = max(3, min(self.N_MAX, n_val))
            p_val = F.calculer_probabilite(n_val)
            self.var_p_affiche.set(f"{p_val:.4f}")
            import math
            self.lbl_formule_p.config(text=f"~ 1.5*ln({n_val})/{n_val}")
        except ValueError:
            self.var_p_affiche.set("auto")
            self.lbl_formule_p.config(text="")

    def statut(self, msg):
        self.var_statut.set(msg)
        self.racine.update_idletasks()

    def _lire_n(self) -> int:
        try:
            n_val = int(self.champ_n.get())
            return max(3, min(self.N_MAX, n_val))
        except ValueError:
            return self.N_DEF

    # --- Logique Principale ---

    def generer(self):
        if self.occupe:
            return
        self.occupe = True
        self.btn_gen.config(state='disabled')
        n_val = self._lire_n()
        p_val = F.calculer_probabilite(n_val)
        self.statut(f"Construction de G({n_val}, p={p_val:.4f})...")
        self.racine.after(50, lambda: self._pipeline(n_val))

    def _pipeline(self, n_val: int):
        self.donnees = F.construire(n_val)
        p_val = self.donnees['probabilite']
        self.var_p_affiche.set(f"{p_val:.4f}")
        self._mettre_a_jour_stats()
        self._dessiner()
        
        nb_cliques = len(self.donnees['cliques'])
        self.statut(f"G({n_val}) genere | {nb_cliques} clique(s) detectee(s)")
        
        self.btn_cliques.config(state='normal')
        self.btn_gen.config(state='normal')
        self.occupe = False

    def _dessiner(self):
        if not self.donnees:
            return
            
        d = self.donnees
        g = d['graphe']
        pos = d['pos']
        roles = d['roles']
        
        # Ensembles pour mettre en évidence les cliques
        sommets_cliques = d['sommets_dans_cliques']
        aretes_cliques = d['aretes_cliques']

        self.ax.clear()
        self.ax.set_facecolor(COULEUR_FOND)
        for sp in self.ax.spines.values():
            sp.set_visible(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        # 1. Dessin du fond (graphe non-clique) très discret
        for u in g:
            for v in g[u]:
                if u < v:
                    cle = (min(u, v), max(u, v))
                    if cle not in aretes_cliques:
                        x = [pos[u][0], pos[v][0]]
                        y = [pos[u][1], pos[v][1]]
                        self.ax.plot(x, y, color='#30363d', lw=0.5, alpha=0.2, zorder=0)

        # 2. Dessin des nœuds non-cliques (petits et gris)
        for s in g:
            if s not in sommets_cliques:
                x, y = pos[s]
                self.ax.scatter(x, y, s=30, c='#484f58', zorder=1, edgecolors='none')

        # 3. Dessin des ARÊTES de cliques (en évidence)
        for u, v in aretes_cliques:
            x = [pos[u][0], pos[v][0]]
            y = [pos[u][1], pos[v][1]]
            self.ax.plot(x, y, color=COULEUR_ACCENT, lw=1.5, alpha=0.8, zorder=2)

        # 4. Dessin des NŒUDS de cliques (en évidence avec rôles)
        for s in sommets_cliques:
            x, y = pos[s]
            role = roles.get(s, 0)
            cfg = CONFIG_ROLES[role]
            couleur = cfg['couleur']
            taille = 120 if s == self.sommet_selectionne else 90
            
            self.ax.scatter(x, y, s=taille, c=couleur, zorder=3,
                            edgecolors='white', linewidths=1.2)
            
            # Étiquette si graphe petit ou si sélectionné
            if len(g) <= 40 or s == self.sommet_selectionne:
                self.ax.text(x, y, str(s), ha='center', va='center',
                             fontsize=7, color='white', zorder=4, fontweight='bold')

        self.canvas_fig.draw()

    def _afficher_accueil(self):
        self.ax.clear()
        self.ax.set_facecolor(COULEUR_FOND)
        for sp in self.ax.spines.values():
            sp.set_visible(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.text(0.5, 0.55,
             "Analyse des Cliques\n\n"
             "Les structures fortement connectees\n"
             "seront mises en evidence.",
            ha='center', va='center', fontsize=13, color=COULEUR_MUTED,
            style='italic', linespacing=1.8, transform=self.ax.transAxes)
        self.ax.text(0.5, 0.30, "Entrez n . Cliquez sur Generer",
            ha='center', va='center', fontsize=10,
            color='#444c56', transform=self.ax.transAxes)
        self.canvas_fig.draw()

    # --- Interactions ---

    def _clic_graphe(self, evt):
        if not self.donnees or evt.xdata is None:
            return
            
        pos = self.donnees['pos']
        
        # Trouver le sommet le plus proche
        proche = min(pos, key=lambda s: (pos[s][0]-evt.xdata)**2 + (pos[s][1]-evt.ydata)**2)
        dist = ((pos[proche][0]-evt.xdata)**2 + (pos[proche][1]-evt.ydata)**2)**0.5

        # Mode vue simple : clic pour info
        if dist < 0.15: 
            self.sommet_selectionne = proche
            self._info_sommet(proche)
        else:
            self.sommet_selectionne = None
        self._dessiner()

    def _info_sommet(self, s: int):
        roles = self.donnees['roles']
        deg = len(self.donnees['graphe'][s])
        role_nom = CONFIG_ROLES[roles.get(s, 0)]['nom']
        est_clique = "Oui" if s in self.donnees['sommets_dans_cliques'] else "Non"
        self.statut(f"Sommet {s} | Role: {role_nom} | Degre: {deg} | Dans Clique: {est_clique}")

    # --- Fonctions d'analyse ---

    def afficher_cliques(self):
        if not self.donnees:
            return
        self.statut("Recherche des cliques (Bron-Kerbosch)...")
        self.racine.update_idletasks()
        cliques = self.donnees['cliques']
        
        if not cliques:
            messagebox.showinfo("Cliques", "Aucune clique de taille >= 3 trouvee.")
        else:
            cliques_tri = sorted(cliques, key=len, reverse=True)[:10]
            lignes = []
            idx = 0
            for c in cliques_tri:
                liste_str = ', '.join(map(str, sorted(c)))
                lignes.append(f"  {idx+1}. {{{liste_str}}} (taille {len(c)})")
                idx += 1
                
            total = len(cliques)
            message_final = f"Total: {total} clique(s) maximale(s)\n\nTop 10:\n" + "\n".join(lignes)
            messagebox.showinfo("Cliques detectees", message_final)
            
        self.statut(f"{len(cliques)} clique(s) trouvee(s)")

    def _mettre_a_jour_stats(self):
        if not self.donnees:
            return
        d = self.donnees
        self.sv['n'].set(str(d['nb_sommets']))
        self.sv['a'].set(str(d['nb_aretes']))
        self.sv['c'].set(str(d['nb_couleurs']))
        self.sv['s'].set(str(len(d['sommets_frauduleux'])))
        
        for role, v in self.dist_vars.items():
            v.set(str(d['compteurs'].get(role, 0)))

    def _fermer(self):
        plt.close('all')
        self.racine.destroy()

if __name__ == '__main__':
    racine = tk.Tk()
    app = Application(racine)
    racine.mainloop()
