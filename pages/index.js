import Head from 'next/head'
import Header from '@components/Header'
import Footer from '@components/Footer'

export default function Home() {
  return (
    <div className="container">
      <Head>
        <title>Challenge Ufolep 38</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
         <p>Bientôt le challenge Ufolep 38 cyclosport sur cette page.</p>
      </main>

      <Footer />
    </div>
  )
}
