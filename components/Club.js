export default function Club({ data }) {
    return <table class="table">
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
}
