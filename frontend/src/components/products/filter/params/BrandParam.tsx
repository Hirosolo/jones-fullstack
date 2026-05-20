import FilterHeaderParam from "../FilterHeaderParam";
import { useProductsState } from "@Contexts/ProductsContext";
import { brandsData } from "@Components/header/MenuLists";

export default function BrandParam() {
  const { filterListings, filterState } = useProductsState();
  const flatBrands = Object.values(brandsData).flat();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    filterListings({ brand: value });
  };

  return (
    <FilterHeaderParam type="Brand">
      <select
        value={filterState.brand || ""}
        onChange={handleChange}
        className="filter-param__select"
      >
        <option value="">All Brands</option>
        {flatBrands.map((b) => (
          <option key={b} value={b}>
            {b}
          </option>
        ))}
      </select>
    </FilterHeaderParam>
  );
}
