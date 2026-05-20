import CategoryPageWithContext, { getStaticProps as originalGetStaticProps } from './[...categoryId]';

export default function CategoryIndex(props: any) {
  // Reuse the same component — it expects categoryId prop.
  return <CategoryPageWithContext {...props} />;
}

export async function getStaticProps(context: any) {
  // Call the original getStaticProps but force the categoryId to ['all']
  const res = await originalGetStaticProps({ params: { categoryId: ['all'] } });
  return res;
}
