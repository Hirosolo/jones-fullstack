import Link from "next/link";
import SEO from "@Components/common/SEO";
import { categories } from "@Components/header/MenuLists";
import { getPathString } from "src/utils";

export default function CategoriesIndex() {
  return (
    <div>
      <SEO title="Categories" />
      <div className="container">
        <h1>All Categories</h1>
        <div className="categories-grid">
          {categories.map((c) => (
            <Link key={c} href={`/category/${getPathString(c)}`}>
              <a className="category-card">{c}</a>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
