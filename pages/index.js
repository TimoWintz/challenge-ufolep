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
    
    <div class="container">
      <Header title="Challenge Ufolep  Isère Cyclosport" />

        <div class="container ml-5 text-center">
          <img src="ufolep.png" class="w-50 m-3"></img>
        </div>
        
        <div class="alert alert-primary" role="alert">
          Dernière mise à jour le {new Date(localData["date"]).toLocaleDateString("fr-FR")}
        </div>
        <p>
          Bienvenue sur la page du Challenge Ufolep Isère Cyclosport, organisé par le comité départemental. Vous trouverez ici le classement du Challenge mis à jour après chaque épreuve du calendrier.
        </p>
        <p>
        Le règlement se trouve <a href="CYCLO Règlement_Challenge_2025_V1_à valider-1.pdf">ici</a>
        </p>

        <h1>Les classements</h1>
        <div class="container p-3">

        <ul class="nav nav-underline">
            <li class="nav-item">
              <a class="nav-link" aria-current="page" href="hommes">Classement Hommes</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" aria-current="page" href="femmes">Classement Femmes</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" aria-current="page" href="jeunes">Classement Jeunes</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" aria-current="page" href="clubs">Classement Clubs</a>
            </li>
          </ul>
        </div>
        
        


        <h1>Le calendrier du Challenge</h1>


        <table class="table">
          <tbody>
            {localData["courses"].map(({ NOM, DATE, CLUB, PASSE }, index) => {
              var condition = PASSE ? 'table-success' : '';
              return (
                  <tr key={NOM} class={condition}>
                    <th scope="row">{NOM}</th>
                  <th scope="row">{new Date(DATE).toLocaleDateString("fr-FR")}</th>
                    <th scope="row">{CLUB}</th>
                  </tr>
                )
            })
            }

          </tbody>
        </table>
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
