import gradio as gr
import subprocess
import os
import matplotlib.pyplot as plt
from scorer import TaskSchedulerScorer
import tempfile


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(BASE_DIR, "build")
BINARY_PATH = os.path.join(BUILD_DIR, "npu_scheduler")


def run_npu(input_file, algorithm):
    if input_file is None:
        return "Please upload input.txt", None, None, None

    input_path = input_file.name

    try:
        process = subprocess.Popen(
            [BINARY_PATH, input_path, "./", "base", "30"],
            cwd=BUILD_DIR
        )
        process.wait()
    except Exception as e:
        return f"Error running scheduler: {e}", None, None, None

    output_txt_path = os.path.join(BUILD_DIR, "output.txt")

    scorer = TaskSchedulerScorer(input_path, output_txt_path)
    score, message, total_time = scorer.calculate_score()

    if scorer.valid:
        fig = scorer.visualize_schedule(save_png=False)

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig.savefig(tmp_file.name, dpi=300, bbox_inches="tight")
        tmp_file.close()
        png_path = tmp_file.name
    else:
        fig = None
        png_path = None

    return message, fig, png_path, output_txt_path


with gr.Blocks(theme=gr.themes.Soft(), title="NPU Scheduler") as demo:

    gr.Markdown(
        """
        # ⚙️ NPU Task Scheduler

        Upload **input.txt** to run the scheduler and visualize the execution timeline.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            input_file = gr.File(label="📄 Upload input.txt")

            algorithm = gr.Dropdown(
                choices=["algo1", "algo2", "algo3"],
                value="base",
                label="⚙️ Select Algorithm"
            )

            run_button = gr.Button("🚀 Run Scheduler", variant="primary")

        with gr.Column(scale=2):
            plot = gr.Plot(label="📊 Schedule Visualization")

    output_text = gr.Textbox(
        label="Result",
        lines=6
    )

    with gr.Row():
        download_png = gr.File(label="⬇ Download PNG")
        download_output = gr.File(label="⬇ Download output.txt")

    run_button.click(
        fn=run_npu,
        inputs=[input_file, algorithm],
        outputs=[output_text, plot, download_png, download_output]
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)