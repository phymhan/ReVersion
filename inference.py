import os
import argparse

import torch
from PIL import Image

from diffusers import StableDiffusionPipeline
from templates.templates import inference_templates

import math

"""
Inference script for generating batch results
"""


def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--prompt",
        type=str,
        help="input a single text prompt for generation",
    )
    parser.add_argument(
        "--template_name",
        type=str,
        help="select a batch of text prompts from templates.py for generation",
    )
    parser.add_argument(
        "--model_id",
        type=str,
        required=True,
        help="absolute path to the folder that contains the trained results",
    )
    parser.add_argument(
        "--placeholder_string",
        type=str,
        default="<R>",
        help="place holder string of the relation prompt",
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=10,
        help="number of samples to generate for each prompt",
    )
    parser.add_argument(
        "--guidance_scale",
        type=float,
        default=7.5,
        help="scale for classifier-free guidance",
    )
    args = parser.parse_args()
    return args


def make_image_grid(imgs, rows, cols):
    assert len(imgs) == rows*cols

    w, h = imgs[0].size
    grid = Image.new('RGB', size=(cols*w, rows*h))
    grid_w, grid_h = grid.size

    for i, img in enumerate(imgs):
        grid.paste(img, box=(i%cols*w, i//cols*h))
    return grid


def main():
    args = parse_args()

    # create inference pipeline
    pipe = StableDiffusionPipeline.from_pretrained(args.model_id,torch_dtype=torch.float16).to("cuda")

    # make directory to save images
    image_root_folder = os.path.join(args.model_id, 'inference')
    os.makedirs(image_root_folder, exist_ok = True)

    if args.prompt is None and args.template_name is None:
        raise ValueError("please input a single prompt through'--prompt' or select a batch of prompts using '--template_name'.")

    # single text prompt
    if args.prompt is not None:
        prompt_list = [args.prompt]
    else:
        prompt_list = []

    if args.template_name is not None:
        # read the selected text prompts for generation
        prompt_list.extend(inference_templates[args.template_name])
        
    for prompt in prompt_list:
        # insert relation prompt <R>
        prompt = prompt.lower().replace("<r>", "<R>").format(args.placeholder_string)

        # make sub-folder
        image_folder = os.path.join(image_root_folder, prompt, 'samples')
        os.makedirs(image_folder, exist_ok = True)

        # batch generation
        images = pipe(prompt, num_inference_steps=50, guidance_scale=args.guidance_scale, num_images_per_prompt=args.num_samples).images

        # save generated images
        for idx, image in enumerate(images):
            image_name = f"{str(idx).zfill(4)}.png"
            image_path = os.path.join(image_folder, image_name)
            image.save(image_path)

        # save a grid of images
        image_grid = make_image_grid(images, rows=2, cols=math.ceil(args.num_samples/2))
        image_grid_path = os.path.join(image_root_folder, prompt, f'{prompt}.png')
        image_grid.save(image_grid_path)


if __name__ == "__main__":
    main()
