type SearchEntityType = "area" | "building" | "project";

interface AutocompleteState {
    id?: string;
    type?: SearchEntityType;
    value: string;
}

type AutocompleteOption = {
    id: string;
    value: string;
    type: SearchEntityType;
};
