JSONType = None | bool | int | float | str | list["JSONType"] | dict[str, "JSONType"]
JSONList = list[JSONType]
JSONDict = dict[str, JSONType]
