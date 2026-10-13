"""
Renders standard LaTeX equations for Qiskit Fall Fest 2026 into assets/qff_phase1_latex_images/
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def render_latex_to_png(formula: str, output_path: Path, fontsize: int = 18):
    fig = plt.figure(figsize=(6, 1.6), dpi=300)
    plt.text(
        0.5, 0.5, f"${formula}$",
        horizontalalignment="center",
        verticalalignment="center",
        fontsize=fontsize,
        color="#0F172A",
    )
    plt.axis("off")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", pad_inches=0.15, transparent=False, facecolor="white")
    plt.close(fig)

def main():
    base_dir = Path(__file__).resolve().parent / "assets" / "qff_phase1_latex_images"
    base_dir.mkdir(parents=True, exist_ok=True)

    equations = {
        "eq_qubit_state.png": r"|\psi\rangle = \alpha|0\rangle + \beta|1\rangle, \quad |\alpha|^2 + |\beta|^2 = 1",
        "eq_bell_state.png": r"|\Phi^+\rangle = \frac{1}{\sqrt{2}}\left(|00\rangle + |11\rangle\right)",
        "eq_graph.png": r"G = (V, E), \quad E \subseteq V \times V, \quad \deg(v) = |\{u \in V : (u,v) \in E\}|",
        "eq_bell_fidelity.png": r"F(\rho, |\Phi^+\rangle) = \langle\Phi^+|\rho|\Phi^+\rangle = \mathrm{Tr}(\rho |\Phi^+\rangle\langle\Phi^+|)",
        "eq_zz_expectation.png": r"\langle Z_i Z_j \rangle = \mathrm{Tr}(\rho \cdot (Z_i \otimes Z_j)) = \frac{1}{N_{\mathrm{shots}}}\sum_{k=1}^{N_{\mathrm{shots}}} s_i^{(k)} s_j^{(k)}",
        "eq_standard_error.png": r"\sigma_p = \sqrt{\frac{p(1 - p)}{N_{\mathrm{shots}}}}, \quad \mathrm{CI}_{95\%} = p \pm 1.96 \cdot \sigma_p",
    }

    for filename, formula in equations.items():
        out_file = base_dir / filename
        render_latex_to_png(formula, out_file)
        print(f"Generated: {out_file.name}")

if __name__ == "__main__":
    main()
