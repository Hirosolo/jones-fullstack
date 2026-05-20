import "@Sass/main.scss";
import "nprogress/nprogress.css";
import "react-toastify/dist/ReactToastify.css";

import { AppProps } from "next/app";
import Head from "next/head";
import { useRouter } from "next/router";
import Router from "next/router";
import NProgress from "nprogress";
import { ToastContainer } from "react-toastify";

import Layout from "@Components/layouts/Layout";
import SEO from "@Components/common/SEO";
import AdminLayout from "@Components/layouts/AdminLayout";
import ErrorBoundary from "@Components/ErrorBoundary";

import { AuthProvider } from "@Contexts/AuthContext";
import { UIProvider } from "@Contexts/UIContext";
import { MOCK_RATES, MOCK_USER } from "@Lib/mockData";

NProgress.configure({ showSpinner: false });
Router.events.on("routeChangeStart", () => NProgress.start());
Router.events.on("routeChangeComplete", () => NProgress.done());
Router.events.on("routeChangeError", () => NProgress.done());

function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const isAdmin = router.pathname.startsWith("/admin");

  return (
    <>
      <UIProvider currencyRates={MOCK_RATES} announcementHidden={false}>
        <AuthProvider currentUser={MOCK_USER}>
          {isAdmin ? (
            <AdminLayout>
              <Component {...pageProps} />
            </AdminLayout>
          ) : (
            <>
              <Head>
                <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
                <meta
                  name="viewport"
                  content="width=device-width, initial-scale=1.0"
                />
              </Head>
              <SEO />
              <Layout>
                <ErrorBoundary>
                  <Component {...pageProps} />
                </ErrorBoundary>
              </Layout>
            </>
          )}
        </AuthProvider>
      </UIProvider>
      <ToastContainer position="bottom-right" hideProgressBar />
    </>
  );
}

export default MyApp;
