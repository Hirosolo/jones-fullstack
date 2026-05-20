import type { ProductComponentType } from "src/types/shared";
import { NextPage, GetServerSideProps } from "next";
import SEO from "@Components/common/SEO";
import Constraints from "@Components/products/constraints";
import ProductsGrid from "@Components/products/ProductsGrid";
import { MOCK_PRODUCTS } from "@Lib/mockData";
import { fetchProducts } from "@Lib/api";
import { categories, brandsData } from "@Components/header/MenuLists";
import { useRouter } from "next/router";

const SearchPage: NextPage<SearchPageType> = ({ query, products, count }) => {
  const router = useRouter();
  const flatBrands = Object.values(brandsData).flat();

  const handleFilterChange = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget as HTMLFormElement);
    const q = form.get("q") || "";
    const category = form.get("category") || "";
    const brand = form.get("brand") || "";
    router.push({ pathname: "/search", query: { q, category, brand } });
  };

  return (
    <div>
      <SEO title={`"${query}"`} />
      <Constraints
        isSearch
        allProductsCount={count}
        currentProductsCount={products.length}
      />

      <div className="search-filters">
        <form onSubmit={handleFilterChange} className="search-filters-form">
          <input name="q" defaultValue={query} placeholder="Search keyword" />
          <select name="category">
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select name="brand">
            <option value="">All Brands</option>
            {flatBrands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
          <button type="submit">Filter</button>
        </form>
      </div>

      <div className="results">
        <div className={"results__container"}>
          <ProductsGrid products={products} />
        </div>
      </div>
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async ({ query }) => {
  const { search = "", q = "", category = "", brand = "" } = query;
  const searchQuery = (search || q) as string;

  let all = MOCK_PRODUCTS;
  try {
    all = await fetchProducts();
  } catch (e) {
    // fallback to mocks
  }

  const results = all.filter((product) => {
    const matchesKeyword = searchQuery
      ? product.title.toLowerCase().includes((searchQuery as string).toLowerCase())
      : true;
    const matchesCategory = category
      ? ((product as any).category && (product as any).category.toLowerCase() === ((category as string).toLowerCase())) ||
        (product.title || "").toLowerCase().includes((category as string).toLowerCase()) ||
        (product.type && String(product.type).toLowerCase().includes((category as string).toLowerCase()))
      : true;
    const matchesBrand = brand
      ? ((product as any).brand && (product as any).brand.toLowerCase() === ((brand as string).toLowerCase())) ||
        (product.title || "").toLowerCase().includes((brand as string).toLowerCase())
      : true;
    return matchesKeyword && matchesCategory && matchesBrand;
  });

  return {
    props: {
      query: searchQuery,
      products: results,
      count: results.length,
    },
  };
};

export default SearchPage;

interface SearchPageType {
  query: string;
  products: ProductComponentType[];
  count: number;
}
