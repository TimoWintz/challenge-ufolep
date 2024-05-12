export default function Club({ data }) {
    return <div class="container">
         <p>            Attribution des points:</p>
        <ul>
            <li>Points individuels: somme des points des coureurs du club</li>
            <li>Points organisations:
                <ul>
                    <li>une épreuve en ligne, cyclocross, grimpée ou CLM : 20 points</li>
                    <li>un Championnat : 25 points</li>
                    <li>une course avec plusieurs étapes le même jour : 30 points</li>
                    <li>une course à étapes sur plusieurs jours : 40 points</li>
                </ul>
            </li>
        </ul>        <table class="table">
       
        <thead>
            <tr>
                <th scope="col">Rang</th>
                <th scope="col">Club</th>
                <th scope="col">Points organisations</th>
                <th scope="col">Points individuels</th>
                <th scope='col'>Total</th>
            </tr>
        </thead>
        <tbody>
            {data.map(({ RANG, CLUB, ORGA, INDIV, TOTAL }, index) => (
                <tr key={CLUB}>
                    <th scope="row">{RANG}</th>
                    <th scope="row">{CLUB}</th>
                    <th scope="row">{ORGA}</th>
                    <th scope="row">{INDIV}</th>
                    <th scope="row">{TOTAL}</th>
                </tr>
            ))}

        </tbody>
        </table>
    </div>
}
