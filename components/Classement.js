const helper_fun = (COURSE, PLACE, POINTS_L, PARTICIPATION_L) => {
    return COURSE.map(({ }, index) => {
        var place = PLACE[index]
        if (place == "1") {
            place = "1er"
        }
        else if (place == "DNF") {
            place = "ab."
        }
        else if (place == "DNS") {
            place = "np."
        }
        else {
            place = place + "ème"
        }
        return place + " " + COURSE[index].replaceAll(" ", " ") + " : " + POINTS_L[index] + "+" + PARTICIPATION_L[index];
    }).join("\n");

}

export default function Classement({ data }) {
    return <div class="container">
            <table class="table table-striped">
                <thead class="bg-light sticky-top">
                    <tr>
                        <th scope="col">Rang</th>
                        <th scope="col">Nom</th>
                        <th scope="col">Club</th>
                        <th scope="col">Points résultats 
                            <button type="button" class="btn badge btn-sm btn-primary " data-bs-trigger="focus" data-bs-toggle="popover" data-bs-title="Points résultats" data-bs-content="Sur chaque course, de 5 à 1 points pour les 5 premiers licenciés Ufolep 38">?</button>
                        </th>
                        <th scope="col">Participations 
                            <button type="button" class="btn badge btn-sm btn-primary " data-bs-trigger="focus" data-bs-toggle="popover" data-bs-title="Points participations" data-bs-content="1 point de participation pour chaque course (y compris abandons)">?</button></th>
                        <th scope='col'>Total</th>
                        <th scope='col'></th>
                    </tr>
                </thead>
                <tbody>
                    {data.map(({ RANG, NOM, CLUB, POINTS, PARTICIPATION, TOTAL, COURSE, PLACE, POINTS_L, PARTICIPATION_L }, index) => (
                        <tr key={NOM} class="align-middle">
                            <th scope="row">{RANG}</th>
                            <th scope="row">{NOM}</th>
                            <th scope="row">{CLUB}</th>
                            <th scope="row">
                                {POINTS}
                            </th>
                            <th scope="row">{PARTICIPATION}</th>
                            <th scope="row">{TOTAL}</th>
                            <th scope="row">
                                <button type="button" class="btn btn-sm btn-light" data-bs-trigger="focus" data-bs-toggle="popover" data-bs-title="Détails des places et points" data-bs-content={helper_fun(COURSE, PLACE, POINTS_L, PARTICIPATION_L)}>Détails</button>
                            </th>

                        </tr>
                    ))}

                </tbody>

            </table>

        </div>
}
