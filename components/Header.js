export default function Header({ title }) {
  return <nav class="navbar sticky-top text-bg-light">
    <div class="container">
    <a class="navbar-brand" href="/">{title}</a>
      <ul class="nav nav-pills">
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
          <a class="nav-link disabled" href="#">Classement clubs (à venir)</a>
          </li>
      </ul>
      </div>
      </nav>
}
