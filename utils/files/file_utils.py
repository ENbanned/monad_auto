import os
import json

def read_json(path: str | tuple | list, encoding: str | None = None) -> list | dict:
    path = join_path(path)
    return json.load(open(path, encoding=encoding))



def update_dict(modifiable: dict, template: dict, rearrange: bool = True, remove_extra_keys: bool = False) -> dict:
    """
    Update the specified dictionary with any number of dictionary attachments based on the template without changing the values already set.

    :param dict modifiable: a dictionary for template-based modification
    :param dict template: the dictionary-template
    :param bool rearrange: make the order of the keys as in the template, and place the extra keys at the end (True)
    :param bool remove_extra_keys: whether to remove unnecessary keys and their values (False)
    :return dict: the modified dictionary
    """
    for key, value in template.items():
        if key not in modifiable:
            modifiable.update({key: value})

        elif isinstance(value, dict):
            modifiable[key] = update_dict(
                modifiable=modifiable[key], template=value, rearrange=rearrange, remove_extra_keys=remove_extra_keys
            )

    if rearrange:
        new_dict = {}
        for key in template.keys():
            new_dict[key] = modifiable[key]

        for key in tuple(set(modifiable) - set(new_dict)):
            new_dict[key] = modifiable[key]

    else:
        new_dict = modifiable.copy()

    if remove_extra_keys:
        for key in tuple(set(modifiable) - set(template)):
            del new_dict[key]

    return new_dict

def write_json(path: str | tuple | list, obj: list | dict, indent: int | None = None,
               encoding: str | None = None) -> None:
    """
    Write Python list or dictionary to a JSON file.

    :param Union[str, tuple, list] path: path to the JSON file
    :param Union[list, dict] obj: the Python list or dictionary
    :param Optional[int] indent: the indent level
    :param Optional[str] encoding: the name of the encoding used to decode or encode the file
    """
    path = join_path(path)
    with open(path, mode='w', encoding=encoding) as f:
        json.dump(obj, f, indent=indent)
        

def read_json(path: str | tuple | list, encoding: str | None = None) -> list | dict:
    path = join_path(path)
    return json.load(open(path, encoding=encoding))

def join_path(path: str | tuple | list) -> str:
    if isinstance(path, str):
        return path
    return str(os.path.join(*path))


def touch(path: str | tuple | list, file: bool = False) -> bool:
    path = join_path(path)
    if file:
        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write('')

            return True

        return False

    if not os.path.isdir(path):
        os.mkdir(path)
        return True

    return False