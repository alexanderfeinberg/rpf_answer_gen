import logging

from answer_gen.utils.file_utils import read_file_async
from answer_gen.utils.generative.parsers import parse_questions_json, parse_answer_json
from answer_gen.exceptions import GenerativeOutputError, GenerativeExecutionError

logger = logging.getLogger(__name__)

async def generate_questions(generative_client, prompt_path : str,
                             model : str, file : bytes):
    """Generate and parse RFP questions from an uploaded file."""
    prompt = await read_file_async(prompt_path)

    try:
        questions_json_text = await generative_client.generate_text_with_file(
            model=model,
            prompt=prompt,
            file=file,
        )
    except Exception as e:
        logger.exception(f'LLM question generation call failed model={model}: {str(e)}')
        raise GenerativeExecutionError('An error occurred when calling Generative model')

    try:
        questions = parse_questions_json(questions_json_text)
    except Exception as e:
        logger.exception("Failed to parse LLM question output")
        raise GenerativeOutputError('An error occured while parsing LLM output.')

    return questions


async def generate_answers(
    generative_client,
    prompt_path: str,
    model: str,
    question_text: str,
    formatting_args : dict | None = None,
) -> list:
    """Generate and parse answer objects for the provided question payload."""
    prompt = await read_file_async(prompt_path)
    formatting_args = formatting_args or {}

    filled_prompt = prompt.format(question = question_text, **formatting_args)

    try:
        answers_json_text = await generative_client.generate_text(
            model=model,
            prompt=filled_prompt,
        )
    except Exception as e:
        logger.exception(f'LLM answer generation call failed model={model}: {str(e)}')
        raise GenerativeExecutionError('An error occured when calling Generative model')

    try:
        answers = parse_answer_json(answers_json_text)
    except Exception as e:
        logger.exception(f'Failed to parse LLM answer output: {str(e)}')
        raise GenerativeOutputError("Failed to parse LLM answers.")

    return answers

async def generate_single_answer(generative_client,
    prompt_path: str,
    model: str,
    question_text: str,
    context: str):
        """Generate a single answer object by selecting the first parsed answer."""
        answers = await generate_answers(generative_client, prompt_path, model, question_text, {"context" : context})
        if answers:
             return answers[0]
