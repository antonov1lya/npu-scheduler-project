# import gradio as gr
# import subprocess
# import os
# import matplotlib.pyplot as plt
# from scorer import TaskSchedulerScorer
# import tempfile

# def run_npu(input_file):
#     if input_file is None:
#         return "", None, None, None
    
#     input_path = input_file.name
#     binary_path = './npu_scheduler'
#     working_dir = './build'

#     output_lines = []

#     try:
#         process = subprocess.Popen(
#             [binary_path, input_path, './', 'base', '30'],
#             cwd=working_dir
#         )
#         process.wait()
#     except Exception as e:
#         return f"Error running npu_scheduler: {str(e)}", None, None, None
    
#     output_txt_path = os.path.join(working_dir, "output.txt")

#     scorer = TaskSchedulerScorer(input_path, output_txt_path)
#     score, message, total_time = scorer.calculate_score()
    
#     output_lines.append(message)
#     stdout_text = "\n".join(output_lines)
    
#     if scorer.valid:
#         fig = scorer.visualize_schedule(save_png=False)

#         tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
#         fig.savefig(tmp_file.name, dpi=300, bbox_inches='tight')
#         tmp_file.close()
#         download_png_path = tmp_file.name
#     else:
#         fig = None
#         download_png_path = None

#     return stdout_text, fig, download_png_path, output_txt_path


# iface = gr.Interface(
#     fn=run_npu,
#     inputs=[
#         gr.File(label="Выберите input.txt"),
#     ],
#     outputs=[
#         gr.Textbox(label="Вывод"),
#         gr.Plot(label="График"),
#         gr.File(label="Скачать график PNG"),
#         gr.File(label="Скачать output.txt")
#     ],
#     title="NPU Scheduler",
#     description="Загрузите input.txt, получите график и возможность скачать результаты"
# )

# if __name__ == "__main__":
#     iface.launch(server_name="0.0.0.0", server_port=7860)
import gradio as gr
import subprocess
import os
import matplotlib.pyplot as plt
from scorer import TaskSchedulerScorer
import tempfile


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(BASE_DIR, "build")
BINARY_PATH = os.path.join(BUILD_DIR, "npu_scheduler")


def run_npu(input_file):
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
        inputs=input_file,
        outputs=[output_text, plot, download_png, download_output]
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)