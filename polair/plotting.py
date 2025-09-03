from __future__ import annotations


# def plot_series(measurements: Iterable[Measurement], title: str="Pomiar", outfile: Optional[str]=None):
#     xs = [m.dt for m in measurements if m.value is not None]
#     ys = [m.value for m in measurements if m.value is not None]
#     fig, ax = plt.subplots()
#     ax.plot(xs, ys, marker="o")
#     ax.set_title(title)
#     ax.set_xlabel("Czas")
#     ax.set_ylabel("Wartość")
#     fig.autofmt_xdate()
#     if outfile:
#         fig.savefig(outfile, bbox_inches="tight")
#     return fig, ax

def plot_series(measurements, title="Pomiary"):
    import matplotlib.pyplot as plt

    xs = [m["dt"] for m in measurements if m.get("value") is not None]
    ys = [m["value"] for m in measurements if m.get("value") is not None]

    fig, ax = plt.subplots()
    ax.plot(xs, ys, marker="o")
    ax.set_title(title)
    ax.set_xlabel("Czas")
    ax.set_ylabel("Wartość")
    fig.autofmt_xdate()
    return fig, ax