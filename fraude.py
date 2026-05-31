import tkinter as tk
from tkinter import ttk
import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random



BG      = '#0d1117'   # fond principal
PANEL   = '#161b22'   # barre latérale
CARD    = '#1c2128'   # cartes/champs
BORDER  = '#30363d'   # séparateurs
TXT     = '#e6edf3'   # texte principal
MUTED   = '#7d8590'   # texte secondaire
ACCENT  = '#2188ff'   # bouton principal


ROLES = {
    0: {
        'name':  'Consommateur',
        'color': '#ff6b6b',
        'shape': 'o',
        'size':  220,
        'char':  'C',
        'info':  'Faible degré · Destinataire final',
    },
    1: {
        'name':  'Fournisseur',
        'color': '#4dabf7',
        'shape': 's',
        'size':  240,
        'char':  'F',
        'info':  'Degré moyen · Intermédiaire',
    },
    2: {
        'name':  'Approvisionneur',
        'color': '#51cf66',
        'shape': '^',
        'size':  260,
        'char':  'A',
        'info':  'Fort degré · Source principale',
    },
    3: {
        'name':  'Suspect / Fraude',
        'color': '#fcc419',
        'shape': 'D',
        'size':  220,
        'char':  'S',
        'info':  'Circuit direct · Irrégulier',
    },
}


class App:
    """Application principale G(n, p) — Détection de Fraude."""

    PLACEHOLDER = "Entrer taille du graphe (n)"
    P           = 0.10   # probabilité fixe
    N_DEFAULT   = 50     # taille par défaut
    N_MAX       = 10000    # taille maximale

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("G(n, p) — Détection de Fraude")
        root.configure(bg=BG)
        root.geometry("1200x730")
        root.minsize(960, 650)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # État du graphe
        self.G:               nx.Graph | None = None
        self.pos:             dict | None     = None
        self.node_roles:      dict            = {}
        self.fraud_nodes:     set             = set()
        self.fraud_edges_set: set             = set()
        self.n_colors:        int             = 0
        self.busy:            bool            = False
        self._after_id:       str | None      = None

        self._build_ui()


    #  CONSTRUCTION DE L'INTERFACE


    def _build_ui(self) -> None:
        # Barre latérale
        self.sidebar = tk.Frame(self.root, bg=PANEL, width=265)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        # Séparateur vertical
        tk.Frame(self.root, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)
        # Zone principale
        main = tk.Frame(self.root, bg=BG)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_main(main)


    def _build_sidebar(self) -> None:
        s   = self.sidebar
        pad = 16

        # En-tête
        self._vspace(s, 20)
        tk.Label(s, text="G(n, p) — Fraude",
                 font=('Courier New', 12, 'bold'),
                 bg=PANEL, fg=TXT, anchor='w').pack(padx=pad, fill=tk.X)
        tk.Label(s, text="Graphe aléatoire · coloration · rôles",
                 font=('Courier New', 8),
                 bg=PANEL, fg=MUTED, anchor='w').pack(padx=pad, fill=tk.X)

        self._divider(s, pad)


        self._section_label(s, "PARAMÈTRES")

        # Champ de saisie avec placeholder
        entry_wrapper = tk.Frame(s, bg=CARD, highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT)
        entry_wrapper.pack(padx=pad - 2, fill=tk.X, pady=(0, 6))
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            entry_wrapper,
            textvariable=self.entry_var,
            font=('Courier New', 11),
            bg=CARD, fg=MUTED,
            insertbackground=TXT,
            relief='flat', bd=9,
        )
        self.entry.pack(fill=tk.BOTH, expand=True)
        self.entry.insert(0, self.PLACEHOLDER)
        self.entry.bind('<FocusIn>',  self._ph_in)
        self.entry.bind('<FocusOut>', self._ph_out)
        self.entry.bind('<Return>',   lambda _e: self.do_generate())

        # Badges d'info
        badges_row = tk.Frame(s, bg=PANEL)
        badges_row.pack(padx=pad - 2, fill=tk.X, pady=(0, 10))
        for txt in [f"p = {self.P} (fixe)", f"défaut : {self.N_DEFAULT}", f"max : {self.N_MAX}"]:
            tk.Label(badges_row, text=txt,
                     font=('Courier New', 8),
                     bg=CARD, fg=MUTED, padx=5, pady=2
                     ).pack(side=tk.LEFT, padx=(0, 4))

        # Bouton Générer
        self.btn_gen = tk.Button(
            s, text=">>   Générer le graphe",
            font=('Courier New', 10, 'bold'),
            bg=ACCENT, fg='#ffffff',
            relief='flat', bd=0, pady=10,
            cursor='hand2',
            command=self.do_generate,
        )
        self.btn_gen.pack(padx=pad - 2, fill=tk.X, pady=(0, 5))
        self._add_hover(self.btn_gen, ACCENT, '#1a6de0')

        # Bouton Recolorer
        self.btn_rc = tk.Button(
            s, text="   Recolorer",
            font=('Courier New', 10),
            bg=CARD, fg=TXT,
            relief='flat', bd=0, pady=9,
            cursor='hand2', state='disabled',
            command=self.do_recolor,
        )
        self.btn_rc.pack(padx=pad - 2, fill=tk.X, pady=(0, 4))
        self._add_hover(self.btn_rc, CARD, '#252c38')

        self._divider(s, pad)

        # ── Légende 
        self._section_label(s, "LÉGENDE DES RÔLES")
        for cfg in ROLES.values():
            row = tk.Frame(s, bg=PANEL)
            row.pack(padx=pad, fill=tk.X, pady=2)
            tk.Label(row, text=cfg['char'],
                     font=('Courier New', 16),
                     bg=PANEL, fg=cfg['color']).pack(side=tk.LEFT)
            col_txt = tk.Frame(row, bg=PANEL)
            col_txt.pack(side=tk.LEFT, padx=8)
            tk.Label(col_txt, text=cfg['name'],
                     font=('Courier New', 9),
                     bg=PANEL, fg=TXT, anchor='w').pack(fill=tk.X)
            tk.Label(col_txt, text=cfg['info'],
                     font=('Courier New', 7),
                     bg=PANEL, fg=MUTED, anchor='w').pack(fill=tk.X)

        self._divider(s, pad)

        # ── Statistiques 
        self._section_label(s, "STATISTIQUES")
        grid = tk.Frame(s, bg=PANEL)
        grid.pack(padx=pad - 2, fill=tk.X)
        self.sv: dict[str, tk.StringVar] = {}
        for i, (key, lbl) in enumerate([
            ('n', 'Nœuds'), ('e', 'Arêtes'),
            ('c', 'Couleurs'), ('f', 'Suspects'),
        ]):
            card = tk.Frame(grid, bg=CARD, padx=4, pady=8)
            card.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky='nsew')
            grid.columnconfigure(i % 2, weight=1)
            self.sv[key] = tk.StringVar(value='—')
            color = '#fcc419' if key == 'f' else TXT
            tk.Label(card, textvariable=self.sv[key],
                     font=('Courier New', 16, 'bold'),
                     bg=CARD, fg=color).pack()
            tk.Label(card, text=lbl,
                     font=('Courier New', 8),
                     bg=CARD, fg=MUTED).pack()

        self._divider(s, pad)

        # ── Distribution 
        self._section_label(s, "DISTRIBUTION")
        self.dist_bars: dict = {}
        for role, cfg in ROLES.items():
            row = tk.Frame(s, bg=PANEL)
            row.pack(padx=pad, fill=tk.X, pady=3)
            hdr = tk.Frame(row, bg=PANEL)
            hdr.pack(fill=tk.X)
            tk.Label(hdr, text=cfg['name'],
                     font=('Courier New', 8),
                     bg=PANEL, fg=MUTED).pack(side=tk.LEFT)
            cnt_var = tk.StringVar(value='0')
            tk.Label(hdr, textvariable=cnt_var,
                     font=('Courier New', 8),
                     bg=PANEL, fg=cfg['color']).pack(side=tk.RIGHT)
            bar_cv = tk.Canvas(row, bg=BORDER, height=4, highlightthickness=0)
            bar_cv.pack(fill=tk.X, pady=(2, 0))
            self.dist_bars[role] = {
                'var':    cnt_var,
                'canvas': bar_cv,
                'color':  cfg['color'],
            }

    # ── Zone principale 
    def _build_main(self, parent: tk.Frame) -> None:
        # Barre de statut (en bas)
        statusbar = tk.Frame(parent, bg=PANEL, height=30)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        statusbar.pack_propagate(False)
        self.status_var = tk.StringVar(
            value="Entrez une taille et cliquez sur Générer")
        tk.Label(
            statusbar, textvariable=self.status_var,
            font=('Courier New', 9), bg=PANEL, fg=MUTED,
        ).pack(side=tk.LEFT, padx=14, pady=6)

        # Figure Matplotlib
        self.fig = plt.Figure(facecolor=BG)
        self.ax  = self.fig.add_axes([0, 0, 1, 1])
        self._reset_ax()

        # Message de bienvenue
        self.ax.text(
            0.5, 0.55,
            "G(n, p) — Détection de Fraude\n\n"
            "c  Consommateur        f  Fournisseur\n"
            "a  Approvisionneur     s  Suspect / Fraude",
            ha='center', va='center',
            fontsize=13, color=MUTED, style='italic',
            linespacing=1.8,
            transform=self.ax.transAxes,
        )
        self.ax.text(
            0.5, 0.30,
            "Entrez n  ·  cliquez sur  >> Générer",
            ha='center', va='center',
            fontsize=10, color='#444c56',
            transform=self.ax.transAxes,
        )

        self.canvas_mpl = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_mpl.get_tk_widget().configure(bg=BG, highlightthickness=0)
        self.canvas_mpl.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_mpl.draw()

    
    #  UTILITAIRES UI
    

    def _vspace(self, w: tk.Widget, h: int) -> None:
        tk.Frame(w, bg=w.cget('bg'), height=h).pack()

    def _divider(self, w: tk.Widget, pad: int) -> None:
        tk.Frame(w, bg=BORDER, height=1).pack(fill=tk.X, padx=pad, pady=10)

    def _section_label(self, w: tk.Widget, txt: str) -> None:
        tk.Label(w, text=txt,
                 font=('Courier New', 7, 'bold'),
                 bg=PANEL, fg=MUTED, anchor='w'
                 ).pack(padx=16, fill=tk.X, pady=(0, 6))

    def _add_hover(self, btn: tk.Button, normal: str, hovered: str) -> None:
        def enter(_e):
            if str(btn['state']) != 'disabled':
                btn.config(bg=hovered)
        def leave(_e):
            if str(btn['state']) != 'disabled':
                btn.config(bg=normal)
        btn.bind('<Enter>', enter)
        btn.bind('<Leave>', leave)

    def _ph_in(self, event: tk.Event) -> None:
        if self.entry.get() == self.PLACEHOLDER:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=TXT)

    def _ph_out(self, event: tk.Event) -> None:
        if not self.entry.get():
            self.entry.insert(0, self.PLACEHOLDER)
            self.entry.config(fg=MUTED)

    def set_status(self, msg: str) -> None:
        self.status_var.set(msg)
        self.root.update_idletasks()

    def _reset_ax(self) -> None:
        self.ax.clear()
        self.ax.set_facecolor(BG)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for sp in self.ax.spines.values():
            sp.set_visible(False)

    def _on_close(self) -> None:
        if self._after_id:
            self.root.after_cancel(self._after_id)
        plt.close('all')
        self.root.destroy()

    
    #  LOGIQUE DU GRAPHE
    

    def _parse_n(self) -> tuple[int, bool]:
        """Lit n depuis le champ, renvoie (valeur, utilise_défaut)."""
        raw = self.entry.get().strip()
        if raw == self.PLACEHOLDER:
            return self.N_DEFAULT, True
        try:
            n = int(raw)
            if n <= 0:
                return self.N_DEFAULT, True
        except ValueError:
            return self.N_DEFAULT, True
        return max(3, min(self.N_MAX, n)), False

    # ── Génération principale
    def do_generate(self) -> None:
        if self.busy:
            return

        n, used_default = self._parse_n()
        if used_default:
            self.set_status(f"Valeur invalide ou négative → défaut : n = {self.N_DEFAULT}")

        self.busy = True
        self.btn_gen.config(state='disabled')
        self.btn_rc.config(state='disabled')
        self.set_status(f"Construction de G({n}, {self.P})...")
        self.root.after(60, lambda: self._generate(n))

    def _generate(self, n: int) -> None:
        """Construit le graphe, calcule layout, coloration, fraude."""

        # ── Génération G(n, p) 
        G = nx.erdos_renyi_graph(n, self.P)

        # ── Garantie de connexité 
        components = list(nx.connected_components(G))
        while len(components) > 1:
            c1 = list(components[0])
            c2 = list(components[1])
            G.add_edge(random.choice(c1), random.choice(c2))
            components = list(nx.connected_components(G))

        self.G = G

        # ── Disposition Spring Layout
        self.set_status("Calcul de la disposition (spring layout)...")
        self.root.update_idletasks()
        k = max(1.5 / (n ** 0.5), 0.4)
        self.pos = nx.spring_layout(
            G, seed=random.randint(0, 9999), k=k,
            iterations=max(25, min(50, 80 - n // 4)),
        )

        # ── Coloration gloutonne 
        coloring = nx.greedy_color(G, strategy='largest_first')
        self.n_colors = max(coloring.values()) + 1 if coloring else 1
        self.node_roles = {nd: min(col, 3) for nd, col in coloring.items()}

        # ── Détection de fraude 
        self.fraud_nodes     = set()
        self.fraud_edges_set = set()

        for u, v in G.edges():
            ru, rv = self.node_roles[u], self.node_roles[v]
            # Circuit direct Consommateur ↔ Approvisionneur = fraude
            if (ru == 0 and rv == 2) or (ru == 2 and rv == 0):
                self.fraud_edges_set.add((min(u, v), max(u, v)))
                self.fraud_nodes.update([u, v])

        for nd, col in coloring.items():
            if col > 2:                  # couleur ≥ 3 → suspect
                self.fraud_nodes.add(nd)

        # ── Lancement de l'animation
        self.set_status("Animation des nœuds...")
        self._animate(list(G.nodes()), list(G.edges()), step=0)

    # ── Animation progressive 
    def _animate(self, nodes: list, edges: list, step: int) -> None:
        n_nd = len(nodes)
        n_ed = len(edges)
        b_nd = max(1, n_nd // 20)
        b_ed = max(1, n_ed // 15) if n_ed else 1
        f_nd = (n_nd + b_nd - 1) // b_nd
        f_ed = (n_ed + b_ed - 1) // b_ed if n_ed else 0

        if step < f_nd:
            # Phase 1 : nœuds progressifs
            cnt = min((step + 1) * b_nd, n_nd)
            self._draw(nodes[:cnt], [], 'build')
            self.set_status(f"Nœuds : {cnt} / {n_nd}")
            self._after_id = self.root.after(
                55, lambda: self._animate(nodes, edges, step + 1))

        elif step < f_nd + f_ed:
            # Phase 2 : arêtes progressives
            idx = step - f_nd
            cnt = min((idx + 1) * b_ed, n_ed)
            self._draw(nodes, edges[:cnt], 'build')
            self.set_status(f"Arêtes : {cnt} / {n_ed}")
            self._after_id = self.root.after(
                35, lambda: self._animate(nodes, edges, step + 1))

        elif step == f_nd + f_ed:
            # Phase 3 : coloration
            self.set_status("Application de la coloration gloutonne...")
            self._draw(nodes, edges, 'color')
            self._after_id = self.root.after(
                750, lambda: self._animate(nodes, edges, step + 1))

        else:
            # Phase 4 : fraude + finalisation
            self.set_status("Détection des fraudes en cours...")
            self._draw(nodes, edges, 'fraud')
            self._update_stats()
            n = len(nodes)
            e = len(edges)
            f = len(self.fraud_nodes)
            self.set_status(
                f"G({n}, {self.P})  ·  {e} arêtes  ·  "
                f"{self.n_colors} couleurs  ·  {f} suspects détectés")
            self.busy = False
            self.btn_gen.config(state='normal')
            self.btn_rc.config(state='normal')

    # ── Rendu Matplotlib 
    def _draw(
        self,
        visible_nodes: list,
        visible_edges: list,
        mode: str,           # 'build' | 'color' | 'fraud'
    ) -> None:
        self._reset_ax()

        if not visible_nodes or self.G is None:
            self.canvas_mpl.draw()
            return

        pos = self.pos
        vn  = set(visible_nodes)

        if mode == 'build':
            # ── Nœuds gris 
            nx.draw_networkx_nodes(
                self.G, pos,
                nodelist=visible_nodes,
                node_color='#3d4451',
                node_size=185, node_shape='o',
                ax=self.ax,
                edgecolors='#0d1117', linewidths=1.2,
            )
            # ── Arêtes grises
            valid_e = [(u, v) for u, v in visible_edges
                       if u in vn and v in vn]
            if valid_e:
                nx.draw_networkx_edges(
                    self.G, pos,
                    edgelist=valid_e,
                    edge_color='#30363d',
                    width=0.7, alpha=0.75, ax=self.ax,
                )

        else:
            # ── Tri des arêtes : normales vs fraude 
            normal_e = []
            fraud_e  = []
            for u, v in visible_edges:
                if (min(u, v), max(u, v)) in self.fraud_edges_set:
                    fraud_e.append((u, v))
                else:
                    normal_e.append((u, v))

            if normal_e:
                nx.draw_networkx_edges(
                    self.G, pos,
                    edgelist=normal_e,
                    edge_color='#30363d',
                    width=0.7, alpha=0.6, ax=self.ax,
                )

            # Arêtes frauduleuses en tiretés orange
            if mode == 'fraud' and fraud_e:
                nx.draw_networkx_edges(
                    self.G, pos,
                    edgelist=fraud_e,
                    edge_color='#fcc419',
                    width=2.2, alpha=0.95,
                    style='--', ax=self.ax,
                )

            # ── Nœuds par rôle (formes différentes) 
            for role, cfg in ROLES.items():
                nlist = [nd for nd in visible_nodes
                         if self.node_roles.get(nd) == role]
                if nlist:
                    nx.draw_networkx_nodes(
                        self.G, pos,
                        nodelist=nlist,
                        node_color=cfg['color'],
                        node_shape=cfg['shape'],
                        node_size=cfg['size'],
                        ax=self.ax,
                        edgecolors='#0d1117',
                        linewidths=1.5,
                        alpha=0.93,
                    )

            # ── Anneaux pulsants autour des nœuds suspects 
            if mode == 'fraud' and self.fraud_nodes:
                fn_vis = [nd for nd in visible_nodes if nd in self.fraud_nodes]
                if fn_vis:
                    xs = [pos[nd][0] for nd in fn_vis]
                    ys = [pos[nd][1] for nd in fn_vis]
                    self.ax.scatter(
                        xs, ys,
                        s=650, c='none',
                        edgecolors='#fcc419', linewidths=1.4,
                        zorder=3, linestyle='--', alpha=0.85,
                    )

        self.canvas_mpl.draw()

    # ── Mise à jour des statistiques 
    def _update_stats(self) -> None:
        if not self.G:
            return
        n = self.G.number_of_nodes()
        e = self.G.number_of_edges()
        f = len(self.fraud_nodes)

        self.sv['n'].set(str(n))
        self.sv['e'].set(str(e))
        self.sv['c'].set(str(self.n_colors))
        self.sv['f'].set(str(f))

        # Barres de distribution
        for role in ROLES:
            cnt = sum(1 for v in self.node_roles.values() if v == role)
            self.dist_bars[role]['var'].set(str(cnt))
            pct = cnt / n if n > 0 else 0
            cv  = self.dist_bars[role]['canvas']
            cv.update_idletasks()
            w = cv.winfo_width()
            if w > 1:
                cv.delete('all')
                fw = int(w * pct)
                if fw > 0:
                    cv.create_rectangle(
                        0, 0, fw, 4,
                        fill=self.dist_bars[role]['color'],
                        outline='',
                    )

    
    #  RECOLORATION
    

    def do_recolor(self) -> None:
        if not self.G or self.busy:
            return

        self.busy = True
        self.btn_gen.config(state='disabled')
        self.btn_rc.config(state='disabled')

        # Stratégie différente à chaque appel → résultats variés
        strategy = random.choice([
            'random_sequential',
            'smallest_last',
            'DSATUR',
            'independent_set',
        ])
        self.set_status(f"Recoloration (stratégie : {strategy})...")

        coloring = nx.greedy_color(self.G, strategy=strategy)
        self.n_colors   = max(coloring.values()) + 1 if coloring else 1
        self.node_roles = {nd: min(col, 3) for nd, col in coloring.items()}

        self.fraud_nodes     = set()
        self.fraud_edges_set = set()
        for u, v in self.G.edges():
            ru, rv = self.node_roles[u], self.node_roles[v]
            if (ru == 0 and rv == 2) or (ru == 2 and rv == 0):
                self.fraud_edges_set.add((min(u, v), max(u, v)))
                self.fraud_nodes.update([u, v])
        for nd, col in coloring.items():
            if col > 2:
                self.fraud_nodes.add(nd)

        nodes = list(self.G.nodes())
        edges = list(self.G.edges())

        # Animation : gris → coloré → fraude
        self._draw(nodes, edges, 'build')

        def _step_color():
            self._draw(nodes, edges, 'color')
            self.set_status("Application des couleurs...")

        def _step_fraud():
            self._draw(nodes, edges, 'fraud')
            self._update_stats()
            f = len(self.fraud_nodes)
            self.set_status(
                f"Recoloré · stratégie : {strategy} · "
                f"{self.n_colors} couleurs · {f} suspects"
            )
            self.busy = False
            self.btn_gen.config(state='normal')
            self.btn_rc.config(state='normal')

        self.root.after(450, _step_color)
        self.root.after(1150, _step_fraud)



#  POINT D'ENTRÉE

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()