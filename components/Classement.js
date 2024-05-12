const helper_fun = (COURSE, PLACE) => {
    return COURSE.map(({ }, index) => {
        return COURSE[index].replaceAll(" ", " ") + " : " + PLACE[index] + "";
    }).join("\n");
   
}

export default function Classement({ data }) {
    return <table class="table">
        <thead>
            <tr>
                <th scope="col">Rang</th>
                <th scope="col">Nom</th>
                <th scope="col">Club</th>
                <th scope="col">Points résultats</th>
                <th scope="col">Participations</th>
                <th scope='col'>Total</th>
                <th scope='col'></th>
            </tr>
        </thead>
        <tbody>
            {data.map(({ RANG, NOM, CLUB, POINTS, PARTICIPATION, TOTAL, COURSE, PLACE }, index) => (
                <tr key={NOM} class="align-middle">
                    <th scope="row">{RANG}</th>
                    <th scope="row">{NOM}</th>
                    <th scope="row">{CLUB}</th>
                    <th scope="row">{POINTS}</th>
                    <th scope="row">{PARTICIPATION}</th>
                    <th scope="row">{TOTAL}</th>
                    <th scope="row">
                        <button type="button" class="btn btn-sm btn-light" data-bs-trigger="focus" data-bs-toggle="popover" data-html="true" data-bs-title="Détails des places" data-bs-content={helper_fun(COURSE, PLACE)}>Détails</button>
                    </th>
                    
                </tr>
            ))}

        </tbody>
    </table>
}
