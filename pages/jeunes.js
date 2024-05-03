import Head from 'next/head'
import Header from '@components/Header'
import Footer from '@components/Footer'
import Classement from '@components/Classement';
import { getIndivData } from '@lib/resultats';
import { Main } from 'next/document';

export async function getStaticProps() {
  const localData = await getIndivData()

  return {
    props: { localData }
  }
}

export default function Home({ localData }) {
  return (
    
    <div className="container">
      <Header title="Challenge Ufolep  Isère Cyclosport" />
      <div class="container-fluid p-3">
        <div class="alert alert-primary" role="alert">
          Dernière mise à jour le {new Date(localData["date"]).toLocaleDateString()}
        </div>
        <Classement data={localData["jeune"]} />
      </div>

      
      
    </div>
    // <div className="container">
    //   <Head>
    //     <link rel="icon" href="/favicon.ico" />
    //   </Head>
      

    //   <div>

    //   { <ul>
    //     {localData["classement"].map(({ NOM, CLUB, TOTAL }) => (
    //       <li>
    //         <b>{NOM} - {CLUB}</b>

    //         <br />
    //         {TOTAL}
    //       </li>
    //     ))}
    //     </ul>}
        
    //     </div>

    //   <Footer />
    // </div>
  )
}
