# Required GUI and plotting libraries
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, StringVar, Checkbutton, IntVar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Valid gear type connections (used for validating user input combinations)
VALID_TRANSITIONS = {
    "Spur": ["Spur", "Helical", "Rack", "Internal"],
    "Helical": ["Spur", "Helical", "Rack", "Internal"],
    "Bevel": ["Bevel", "Miter", "Spiral Bevel"],
    "Miter": ["Bevel", "Miter"],
    "Spiral Bevel": ["Bevel", "Spiral Bevel"],
    "Worm": ["Spur"],
    "Rack": [],
    "Internal": ["Spur", "Helical"]
}

# Unit conversion dictionary for different length and torque units
UNIT_CONVERSIONS = {
    "length": {"mm": 1, "cm": 10, "m": 1000, "inch": 25.4, "ft": 304.8},
    "torque": {"Nm": 1, "kgm": 9.80665, "lbf-ft": 1.35582, "lbf-in": 0.1129848}
}

# Main class to build the GearMatrix Pro GUI and logic
class GearMatrixPro:
    def __init__(self, root):
        self.root = root
        self.root.title("⚙️ GearMatrix Pro — Advanced Gear Calculator")
        self.root.geometry("1300x700")

        # Variables for unit selections
        self.unit_var = tk.StringVar(value="mm")
        self.torque_unit_var = tk.StringVar(value="Nm")
        self.unit_label_var = tk.StringVar(value="Radius (mm)")
        self.unit_var.trace_add("write", self.update_unit_label)
        self.lines = []

        # LEFT FRAME: For input fields
        self.left_frame = tk.Frame(self.root, bg="#111d40", padx=12, pady=12)
        self.left_frame.place(relwidth=0.5, relheight=1.0)

        tk.Label(self.left_frame, text="GearMatrix Pro", font=("Segoe UI", 20, "bold"), fg="#00e5ff", bg="#111d40").pack(pady=5)

        # Unit selection dropdowns
        unit_frame = tk.Frame(self.left_frame, bg="#111d40")
        unit_frame.pack(pady=5)
        tk.Label(unit_frame, text="Length Unit:", fg="#00ccff", bg="#111d40").pack(side="left")
        ttk.Combobox(unit_frame, values=list(UNIT_CONVERSIONS["length"].keys()), state="readonly", width=6, textvariable=self.unit_var).pack(side="left", padx=(5, 15))
        tk.Label(unit_frame, text="Torque Unit:", fg="#00ccff", bg="#111d40").pack(side="left")
        ttk.Combobox(unit_frame, values=list(UNIT_CONVERSIONS["torque"].keys()), state="readonly", width=7, textvariable=self.torque_unit_var).pack(side="left")

        # Input header: Gear type, teeth, radius, connections
        self.input_frame = tk.Frame(self.left_frame, bg="#111d40")
        self.input_frame.pack(pady=5, fill="x")
        header = tk.Frame(self.input_frame, bg="#111d40")
        header.pack(fill="x")
        headers = ["Gear", "Type", "Teeth", "Radius", "Connects To"]
        col_widths = [12, 12, 8, 10, 20]
        for i, (txt, w) in enumerate(zip(headers, col_widths)):
            tk.Label(header, text=txt, width=w, bg="#111d40", fg="#00ccff", anchor="w").grid(row=0, column=i)

        self.gear_rows = []
        self.add_gear_row()  # Add first gear input row by default

        # Add gear button
        tk.Button(self.left_frame, text="+ Add Gear", command=self.add_gear_row, bg="#00ffcc", fg="#000", font=("Segoe UI", 10, "bold"), relief="flat").pack(pady=6)

        # RPM and Torque input fields
        self.rpm_var = tk.StringVar()
        self.torque_var = tk.StringVar()
        entry_frame = tk.Frame(self.left_frame, bg="#111d40")
        entry_frame.pack(pady=10)
        tk.Label(entry_frame, text="Initial RPM:", fg="#00e5ff", bg="#111d40").grid(row=0, column=0, sticky='e')
        tk.Entry(entry_frame, textvariable=self.rpm_var, width=10, bg="#1f2f50", fg="white").grid(row=0, column=1)
        tk.Label(entry_frame, text="Torque:", fg="#00e5ff", bg="#111d40").grid(row=1, column=0, sticky='e')
        tk.Entry(entry_frame, textvariable=self.torque_var, width=10, bg="#1f2f50", fg="white").grid(row=1, column=1)

        # Calculate Button
        tk.Button(self.left_frame, text="▶ Calculate", command=self.calculate, bg="#00ff99", fg="#000", font=("Segoe UI", 11, "bold"), relief="flat").pack(pady=10)

        # RIGHT FRAME: For output display and chart
        self.right_frame = tk.Frame(self.root, bg="#000c1c", padx=10, pady=10)
        self.right_frame.place(relx=0.5, relwidth=0.5, relheight=1.0)

        # Output display label
        self.result_label = tk.Label(self.right_frame, text="Results will appear here...", fg="#00ffaa", bg="#000c1c", font=("Courier New", 10), justify="left")
        self.result_label.pack(anchor="nw", fill="x", pady=10)

        # Matplotlib Figure setup
        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor="#111111")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#111111")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")
        self.ax.grid(True, color="#333333")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Hover tooltip for graph points
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="#222", ec="white"),
                                      color="white", fontsize=9)
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.hover)

    # Update label dynamically when unit is changed
    def update_unit_label(self, *args):
        self.unit_label_var.set(f"Radius ({self.unit_var.get()})")

    # Unit conversion helpers
    def convert_unit_length(self, value):
        return float(value) * UNIT_CONVERSIONS["length"][self.unit_var.get()]

    def convert_unit_torque(self, value):
        return float(value) * UNIT_CONVERSIONS["torque"][self.torque_unit_var.get()]

    # Open multi-select popup to connect gear i to multiple other gears
    def open_multiselect_popup(self, combo_var, idx):
        popup = Toplevel(self.root)
        popup.title(f"Select Connections for Gear {idx}")
        popup.geometry("300x300")
        tk.Label(popup, text="Select gears to connect:").pack(pady=5)

        checks = []
        check_vars = []
        for i in range(len(self.gear_rows)):
            if i != idx:
                var = IntVar()
                chk = Checkbutton(popup, text=f"Gear {i}", variable=var)
                chk.pack(anchor="w")
                checks.append(chk)
                check_vars.append((i, var))

        def apply():
            selected = [str(i) for i, var in check_vars if var.get()]
            combo_var.set(",".join(selected))
            popup.destroy()

        tk.Button(popup, text="Apply", command=apply).pack(pady=10)

    # Refresh the connection fields on each new gear row
    def refresh_connection_dropdowns(self):
        for i, row in enumerate(self.gear_rows):
            row["connects"].unbind("<Button-1>")
            row["connects"].bind("<Button-1>", lambda e, idx=i, var=row["conn_var"]: self.open_multiselect_popup(var, idx))

    # Add a new gear input row
    def add_gear_row(self):
        idx = len(self.gear_rows)
        row_frame = tk.Frame(self.input_frame, bg="#111d40")
        row_frame.pack(pady=2, fill="x")

        gear_label = tk.Label(row_frame, text=f"Gear {idx}", width=12, bg="#111d40", fg="#ffffff")
        gear_label.grid(row=0, column=0, padx=2)

        gear_type = ttk.Combobox(row_frame, values=list(VALID_TRANSITIONS.keys()), state="readonly", width=12)
        gear_type.set("Spur")
        gear_type.grid(row=0, column=1, padx=2)

        teeth_entry = tk.Entry(row_frame, width=8, bg="#1f2f50", fg="#ffffff")
        teeth_entry.insert(0, "20")
        teeth_entry.grid(row=0, column=2, padx=2)

        radius_entry = tk.Entry(row_frame, width=10, bg="#1f2f50", fg="#ffffff")
        radius_entry.insert(0, "50")
        radius_entry.grid(row=0, column=3, padx=2)

        conn_var = StringVar()
        conn_combo = ttk.Combobox(row_frame, width=20, textvariable=conn_var)
        conn_combo.grid(row=0, column=4, padx=2)

        for widget in [gear_type, teeth_entry, radius_entry, conn_combo]:
            widget.bind("<Return>", lambda e, w=widget: w.tk_focusNext().focus())

        self.gear_rows.append({
            "label": gear_label,
            "type": gear_type,
            "teeth": teeth_entry,
            "radius": radius_entry,
            "connects": conn_combo,
            "conn_var": conn_var
        })

        self.refresh_connection_dropdowns()

    # Tooltip display when hovering over the matplotlib chart
    def hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            for line in self.lines:
                cont, ind = line.contains(event)
                if cont:
                    x, y = line.get_data()
                    index = ind["ind"][0]
                    self.annot.xy = (x[index], y[index])
                    self.annot.set_text(f"{line.get_label()}: {y[index]:.2f}")
                    self.annot.set_visible(True)
                    self.canvas.draw_idle()
                    return
        if vis:
            self.annot.set_visible(False)
            self.canvas.draw_idle()

    # Cycle detection for graph connections (avoids infinite loops)
    def has_cycle(self, graph):
        visited = set()
        rec_stack = set()
        def visit(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if visit(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False
        for node in graph:
            if node not in visited:
                if visit(node):
                    return True
        return False

    # Main RPM-Torque calculation and plotting
    def calculate(self):
        try:
            rpm = float(self.rpm_var.get())
            torque = self.convert_unit_torque(self.torque_var.get())
            result = ""

            # Gear graph creation from inputs
            graph = {}
            gear_data = {}

            for i, gear in enumerate(self.gear_rows):
                t = int(gear["teeth"].get())
                r = self.convert_unit_length(gear["radius"].get())
                module = r / t if t else 0
                conn = gear["connects"].get()
                connects = [int(c.strip()) for c in conn.split(',') if c.strip().isdigit()]
                graph[i] = connects
                gear_data[i] = {"teeth": t, "radius": r, "rpm": None, "torque": None, "eff": None, "module": module}

            if self.has_cycle(graph):
                raise ValueError("Cycle detected in gear connections. Remove circular references.")

            # Initialize gear 0 as input
            gear_data[0]["rpm"] = rpm
            gear_data[0]["torque"] = torque
            visited = set()
            result_list = []

            # DFS to traverse connected gears and propagate RPM/Torque
            def dfs(node):
                visited.add(node)
                for nbr in graph.get(node, []):
                    if nbr in visited: continue
                    t1 = gear_data[node]["teeth"]
                    t2 = gear_data[nbr]["teeth"]
                    r1 = gear_data[node]["radius"]
                    r2 = gear_data[nbr]["radius"]
                    radius_ratio = r2 / r1 if r1 else 1
                    rpm_n = gear_data[node]["rpm"] * radius_ratio
                    torque_n = gear_data[node]["torque"] / radius_ratio
                    input_power = gear_data[node]["torque"] * gear_data[node]["rpm"]
                    output_power = torque_n * rpm_n
                    eff = output_power / input_power if input_power else 1
                    gear_data[nbr]["rpm"] = rpm_n
                    gear_data[nbr]["torque"] = torque_n
                    gear_data[nbr]["eff"] = eff
                    result_list.append(f"Gear {node} → Gear {nbr}: Ratio {t2/t1:.2f}, RPM {rpm_n:.2f}, Torque {torque_n:.2f}, Efficiency: {eff*100:.2f}%")
                    dfs(nbr)

            dfs(0)

            # Format output text
            result += "\n".join(result_list)
            last_gear = max((k for k, v in gear_data.items() if v['rpm'] is not None), default=0)
            result += f"\n\n★ Final Gear {last_gear}:\n    RPM: {gear_data[last_gear]['rpm']:.2f} RPM\n    Torque: {gear_data[last_gear]['torque']:.2f} Nm"
            result += "\n\n★ Module Calculations:"
            for i in gear_data:
                result += f"\n    Gear {i}: Module = {gear_data[i]['module']:.2f} {self.unit_var.get()}"
            self.result_label.config(text=result)

            # Plot graph
            self.ax.clear()
            self.ax.set_facecolor("#111111")
            stages = list(gear_data.keys())
            rpms = [gear_data[i]['rpm'] or 0 for i in stages]
            torques = [gear_data[i]['torque'] or 0 for i in stages]
            line1, = self.ax.plot(stages, rpms, marker='o', label='RPM', color='cyan')
            line2, = self.ax.plot(stages, torques, marker='s', label='Torque (Nm)', color='magenta')
            self.lines = [line1, line2]

            self.ax.set_title('Gearwise RPM & Torque')
            self.ax.set_xlabel('Gear Index')
            self.ax.set_ylabel('Values')
            self.ax.grid(True, color="#333333")
            self.ax.tick_params(colors="white")
            self.ax.xaxis.label.set_color("white")
            self.ax.yaxis.label.set_color("white")
            self.ax.title.set_color("white")
            self.ax.legend()
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", f"Input error: {e}")

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = GearMatrixPro(root)
    root.mainloop()
