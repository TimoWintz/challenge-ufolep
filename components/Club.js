const desc_orga = "une épreuve en ligne, cyclocross, grimpée ou CLM: 20 points\nun Championnat: 25 points\nune course avec plusieurs étapes le même jour: 30 points\nune course à étapes sur plusieurs jours: 40 points";

export default function Club({ data }) {
    return <div class="container">

            <table class="table table-striped">

            <thead class="bg-light sticky-top">
            <tr>
                <th scope="col">Rang</th>
                <th scope="col">Club</th>
                        <th scope="col">Points organisations 
                            <button type="button" class="btn badge btn-sm btn-primary " data-bs-trigger="focus" data-bs-toggle="popover" data-bs-title="Points organisations" data-bs-content={desc_orga}>?</button>
                        </th>
                        <th scope="col">Points individuels 
                            <button type="button" class="btn badge btn-sm btn-primary " data-bs-trigger="focus" data-bs-toggle="popover" data-bs-title="Points individuels" data-bs-content="Somme des points des coureurs du club">?</button>
                        </th>
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
