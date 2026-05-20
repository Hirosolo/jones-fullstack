import { useState } from "react";
import FilterHeaderParam from "../FilterHeaderParam";
import { useProductsState } from "@Contexts/ProductsContext";

export default function KeywordParam() {
  const { filterListings, filterState } = useProductsState();
  const [keyword, setKeyword] = useState(filterState.keyword || "");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setKeyword(value);
    filterListings({ keyword: value });
  };

  return (
    <FilterHeaderParam type="Keyword">
      <input
        type="text"
        placeholder="Search products..."
        value={keyword}
        onChange={handleChange}
        className="filter-param__input"
      />
    </FilterHeaderParam>
  );
}
