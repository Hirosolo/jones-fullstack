import FilterHeaderParam from "../FilterHeaderParam";
import { useProductsState } from "@Contexts/ProductsContext";
import { categories } from "@Components/header/MenuLists";

export default function CategoryParam() {
  const { filterListings, filterState } = useProductsState();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    filterListings({ category: value });
  };

  return (
    <FilterHeaderParam type="Category">
      <select
        value={filterState.category || ""}
        onChange={handleChange}
        className="filter-param__select"
      >
        <option value="">All Categories</option>
        {categories.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
    </FilterHeaderParam>
  );
}
