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
            </tr>
        </thead>
        <tbody>
            {data.map(({ RANG, NOM, CLUB, POINTS, PARTICIPATION, TOTAL }, index) => (
                <tr key={NOM}>
                    <th scope="row">{RANG}</th>
                    <th scope="row">{NOM}</th>
                    <th scope="row">{CLUB}</th>
                    <th scope="row">{POINTS}</th>
                    <th scope="row">{PARTICIPATION}</th>
                    <th scope="row">{TOTAL}</th>
                </tr>
            ))}

        </tbody>
    </table>
}
