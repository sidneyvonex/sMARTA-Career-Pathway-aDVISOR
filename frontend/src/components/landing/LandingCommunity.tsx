const SCHOOLS = [
  {
    name: 'Chinga Boys High School',
    county: 'Nyeri County',
    image: '/img/chinga-boys.jpg',
    alt: 'Students at Chinga Boys High School',
  },
  {
    name: 'Alliance High School',
    county: 'Kiambu County',
    image: '/img/alliance-biology.jpg',
    alt: 'Biology class at Alliance High School',
  },
  {
    name: 'Alliance Girls High School',
    county: 'Kiambu County',
    image: '/img/alliance-girls-dining.jpg',
    alt: 'Alliance Girls High School dining hall',
  },
  {
    name: "Mang'u High School",
    county: 'Kiambu County',
    image: '/img/mangu-students.jpg',
    alt: "Students at Mang'u High School",
  },
  {
    name: 'Gachoire Girls High School',
    county: 'Kiambu County',
    image: '/img/gachoire-compound.jpg',
    alt: 'View of the school compound at Gachoire Girls High School',
  },
  {
    name: 'Kiambu High School',
    county: 'Kiambu County',
    image: '/img/kiambu-high.jpg',
    alt: 'Academic complex at Kiambu High School',
  },
  {
    name: 'Kagumo High School',
    county: 'Nyeri County',
    image: '/img/kagumo-high.jpg',
    alt: 'Kagumo High School',
  },
  {
    name: 'Mahiga Girls Secondary School',
    county: 'Nyeri County',
    image: '/img/mahiga-girls.jpg',
    alt: 'Pupils at Mahiga Girls Secondary School',
  },
]

export default function LandingCommunity() {
  return (
    <div id="community" className="landing-community">
      <span className="landing-eyebrow">Central Kenya</span>
      <h2 className="landing-section__heading" style={{ marginTop: '0.75rem' }}>
        Real classrooms. Real learners.
      </h2>
      <p className="landing-community__lede">
        Every school below is real — Kiambu and Nyeri counties, part of the same five-county
        region Smarta Shauri currently supports. Hover a photo for details.
      </p>

      <div className="landing-school-grid">
        {SCHOOLS.map((school) => (
          <figure className="landing-school-card" tabIndex={0} key={school.name}>
            <img src={school.image} alt={school.alt} loading="lazy" />
            <figcaption className="landing-school-card__overlay">
              <span className="landing-school-card__name">{school.name}</span>
              <span className="landing-school-card__meta">{school.county}</span>
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  )
}
