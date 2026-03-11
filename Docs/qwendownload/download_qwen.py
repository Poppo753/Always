from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

model_name = "Qwen/Qwen2.5-VL-7B-Instruct"

print("Downloading model...")

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_name,
    device_map="auto"
)

processor = AutoProcessor.from_pretrained(model_name)

print("Qwen2.5-VL downloaded successfully.")