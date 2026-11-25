lazy from types import ModuleType

from pydantic import BaseModel


def type_name(annotation: object) -> str:
    """int, str | None 这样的写法, 而不是 <class 'int'>.

    Returns:
        类型的写法.

    """
    return annotation.__name__ if isinstance(annotation, type) else str(annotation).replace("typing.", "")


def describe(serializer: type[BaseModel]) -> dict:
    """一个模型的字段契约: 必须有什么, 可以有什么. 派生字段 (computed_field) 只出现在响应里, 标为 computed.

    Returns:
        {字段: {type, required, computed}}.

    """
    fields = {
        info.alias or name: {"type": type_name(info.annotation), "required": info.is_required(), "computed": False}
        for name, info in serializer.model_fields.items()
    }
    for name, info in serializer.model_computed_fields.items():
        fields[info.alias or name] = {"type": type_name(info.return_type), "required": True, "computed": True}
    return fields


def serializer_contract(*modules: ModuleType) -> dict:
    """模块里定义的所有 Pydantic 模型的字段契约: {"模块.类名": {字段: {type, required, computed}}}.

    字段的类型和必填与否是从声明推导出来的, 升级 Pydantic 可能在代码没有任何改动的情况下改变它.

    Returns:
        每个模型的字段契约.

    """
    contract = {}
    for module in modules:
        for name, value in sorted(vars(module).items()):
            if isinstance(value, type) and issubclass(value, BaseModel) and value.__module__ == module.__name__:
                contract[f"{module.__name__}.{name}"] = describe(value)
    return contract
