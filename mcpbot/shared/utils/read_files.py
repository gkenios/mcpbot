from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import Any
import yaml

from jinja2 import Template


class File(ABC):
    @classmethod
    @abstractmethod
    def read_file(cls, path: str) -> Any:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def write_file(cls, path: str, content: Any) -> None:
        raise NotImplementedError


class YamlFile(File):
    @classmethod
    def read_file(cls, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
        return content

    @classmethod
    def write_file(cls, path: str, content: dict[Any, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(content, f, allow_unicode=True, default_flow_style=False)


class JsonFile(File):
    @classmethod
    def read_file(cls, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
        return content

    @classmethod
    def write_file(cls, path: str, content: dict[Any, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=4)


def read_file(
    file_path: str | Path,
    context: dict[str, Any] | None = None,
) -> Any:
    """Reads a file of the type .yaml, .yml or .json and returns the content."""
    obj: type[File]
    if isinstance(file_path, Path):
        file_path = str(file_path)
    if file_path.endswith(".yaml") or file_path.endswith(".yml"):
        obj = YamlFile
    elif file_path.endswith(".json"):
        obj = JsonFile
    else:
        raise ValueError("Unsupported file type")
    data = obj.read_file(file_path)
    if context:
        return render_dict_with_jinja(data, context)
    return data


def write_file(file_path: str, content: Any) -> None:
    """Writes a file of the type .yaml, .yml or .json."""
    obj: type[File]
    if file_path.endswith(".yaml") or file_path.endswith(".yml"):
        obj = YamlFile
    elif file_path.endswith(".json"):
        obj = JsonFile
    else:
        raise ValueError("Unsupported file type")
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    obj.write_file(file_path, content)


def render_dict_with_jinja(
    data: Any,
    context: dict[str, str],
) -> Any:
    """Recursively renders a dictionary structure with Jinja2 templates.

    Args:
        data: The data (loaded as a dictionary).
        context: A dictionary containing the values to replace the placeholders.

    Returns:
        The rendered data (as a Python object).
    """

    def _render(data: Any, context: dict[str, str]) -> Any:
        if isinstance(data, dict):
            new_data = dict()
            for key, value in data.items():
                # Recurse for dict values
                new_data[key] = _render(value, context)
            return new_data
        elif isinstance(data, list):
            # Recurse for list items
            return [_render(item, context) for item in data]
        elif isinstance(data, str):
            try:
                template = Template(data)
                return template.render(context)
            except Exception as error:
                raise Exception(f"Jinja2 error parsing: \n{data}") from error
        else:
            return data

    return _render(data, context)
