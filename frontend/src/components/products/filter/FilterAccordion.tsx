import { IoIosArrowBack } from "react-icons/io";

import Button from "@Components/formControls/Button";
import KeywordParam from "./params/KeywordParam";
import CategoryParam from "./params/CategoryParam";
import BrandParam from "./params/BrandParam";

import { useProductsState } from "@Contexts/ProductsContext";

export default function FilterAccordion({ active, setState }: PropTypes) {
  const { clearFilters } = useProductsState();

  return (
    <div className={"filter" + (active ? " filter--active" : "")}>
      <div className="filter__head">
        <span>Filter</span>
        <button
          aria-label="hide filter"
          onClick={() => setState(false)}
          className="filter__hide"
        >
          <IoIosArrowBack />
        </button>
      </div>

      <KeywordParam />
      <CategoryParam />
      <BrandParam />

      <div className="filter__confirm">
        <Button
          onClick={clearFilters}
          type="submit"
          className="filter__clear-all"
        >
          clear filters
        </Button>
      </div>
    </div>
  );
}

interface PropTypes {
  active: boolean;
  setState: (state: boolean) => void;
}
