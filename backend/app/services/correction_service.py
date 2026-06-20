import re
from functools import lru_cache

from app.core.config import settings

FILLERS = {
    "um",
    "uh",
    "erm",
    "ah",
    "ಅಂ",
    "ಅಮ್",
}

EMPHASIS_WORDS = {
    "very",
    "really",
    "so",
    "too",
    "ಬಹಳ",
    "ತುಂಬಾ",
}


@lru_cache(maxsize=1)
def _load_llm_pipeline():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    tokenizer = AutoTokenizer.from_pretrained(settings.qwen_model_name)
    model = AutoModelForCausalLM.from_pretrained(
        settings.qwen_model_name,
        torch_dtype="auto",
        device_map="auto",
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)


class IntentPreservingCorrectionService:
    def correct(self, transcript: str, language: str | None = None) -> str:
        cleaned = self.deterministic_cleanup(transcript)
        if not settings.enable_llm_editor:
            return cleaned

        try:
            llm_output = self._llm_cleanup(cleaned, language)
        except Exception:
            return cleaned

        llm_output = self._strip_model_output(llm_output)
        if not llm_output:
            return cleaned
        return self.deterministic_cleanup(llm_output)

    def deterministic_cleanup(self, transcript: str) -> str:
        return self._deterministic_cleanup(transcript)

    def _llm_cleanup(self, transcript: str, language: str | None) -> str:
        generator = _load_llm_pipeline()
        prompt = (
            "You are an accessibility text editor for Kannada and English speech transcripts.\n"
            "Task: remove only stuttering repetitions, repeated syllable fragments, fillers, "
            "and grammar errors directly caused by disfluency.\n"
            "Rules: do not paraphrase, summarize, add facts, remove meaningful information, "
            "or change the user's style. Preserve intentional emphasis such as 'very very'.\n"
            f"Language hint: {language or 'unknown'}\n"
            f"Transcript: {transcript}\n"
            "Corrected transcript:"
        )
        result = generator(
            prompt,
            max_new_tokens=min(256, max(32, len(transcript.split()) * 4)),
            do_sample=False,
            temperature=0.0,
            return_full_text=False,
        )
        return str(result[0]["generated_text"]).strip()

    def _strip_model_output(self, text: str) -> str:
        first_line = text.strip().splitlines()[0].strip()
        return first_line.strip('"').strip("'").strip()

    def _deterministic_cleanup(self, transcript: str) -> str:
        text = transcript.strip()
        text = self._remove_stretched_initials(text)
        tokens = text.split()
        tokens = self._remove_fillers(tokens)
        tokens = self._remove_partial_word_repetitions(tokens)
        tokens = self._remove_repeated_tokens(tokens)
        tokens = self._remove_repeated_phrases(tokens)
        return self._normalize_spacing(" ".join(tokens))

    def _remove_fillers(self, tokens: list[str]) -> list[str]:
        return [token for token in tokens if self._clean_token(token).lower() not in FILLERS]

    def _remove_repeated_tokens(self, tokens: list[str]) -> list[str]:
        result: list[str] = []
        for token in tokens:
            normalized = self._clean_token(token).casefold()
            previous = self._clean_token(result[-1]).casefold() if result else ""
            if result and normalized == previous and normalized not in EMPHASIS_WORDS:
                continue
            if result and self._is_prefix_fragment(previous, normalized):
                result[-1] = token
                continue
            result.append(token)
        return result

    def _remove_repeated_phrases(self, tokens: list[str]) -> list[str]:
        if len(tokens) < 4:
            return tokens
        result = tokens[:]
        changed = True
        while changed:
            changed = False
            for size in range(3, 1, -1):
                index = 0
                next_result: list[str] = []
                while index < len(result):
                    current = result[index : index + size]
                    following = result[index + size : index + (2 * size)]
                    if len(current) == size and self._tokens_equal(current, following):
                        next_result.extend(current)
                        index += 2 * size
                        changed = True
                    else:
                        next_result.append(result[index])
                        index += 1
                result = next_result
        return result

    def _remove_partial_word_repetitions(self, tokens: list[str]) -> list[str]:
        result: list[str] = []
        for token in tokens:
            parts = re.split(r"-+", token)
            if len(parts) > 1:
                final = parts[-1]
                prefix_parts = parts[:-1]
                if all(self._is_prefix_fragment(part, final) for part in prefix_parts):
                    result.append(final)
                    continue
            normalized = self._clean_token(token).casefold()
            if result and self._clean_token(result[-1]).casefold() == normalized and normalized not in EMPHASIS_WORDS:
                continue
            if result and self._is_prefix_fragment(self._clean_token(result[-1]), self._clean_token(token)):
                result[-1] = token
                continue
            result.append(token)
        return result

    def _remove_stretched_initials(self, text: str) -> str:
        return re.sub(r"\b([A-Za-z])\1{2,}([A-Za-z]+)", lambda m: m.group(1) + m.group(2), text)

    def _is_prefix_fragment(self, fragment: str, word: str) -> bool:
        fragment = fragment.casefold().strip()
        word = word.casefold().strip()
        if not fragment or not word or fragment == word:
            return False
        return len(fragment) <= max(4, len(word) // 2) and word.startswith(fragment)

    def _tokens_equal(self, left: list[str], right: list[str]) -> bool:
        if len(left) != len(right):
            return False
        return [self._clean_token(item).casefold() for item in left] == [
            self._clean_token(item).casefold() for item in right
        ]

    def _clean_token(self, token: str) -> str:
        return token.strip(".,!?;:\"'()[]{}")

    def _normalize_spacing(self, text: str) -> str:
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
