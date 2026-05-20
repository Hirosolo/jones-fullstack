import Link from "next/link";
import SEO from "@Components/common/SEO";
import { brandsData } from "@Components/header/MenuLists";
import { getPathString } from "src/utils";

export default function BrandsIndex() {
  const flatBrands = Object.values(brandsData).flat();
  return (
    <div>
      <SEO title="Brands" />
      <div className="container">
        <h1>All Brands</h1>
        <div className="brands-grid">
          {flatBrands.map((b) => (
            <Link key={b} href={`/brand/${getPathString(b)}`}>
              <a className="brand-card">{b}</a>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
