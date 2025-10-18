import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';
import { makeStyles, shorthands } from '@fluentui/react-components';
import { bundleIcon, ChatSparkle24Filled, ChatSparkle24Regular, Grid24Filled, Grid24Regular, Map24Filled, Map24Regular, PeopleTeam24Filled, PeopleTeam24Regular, ShieldGlobe24Filled, ShieldGlobe24Regular } from '@fluentui/react-icons';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Text from '../components/ui/Text';

const useStyles = makeStyles({
  hero: {
    display: 'grid',
    gap: '32px',
    alignItems: 'center',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    ...shorthands.padding('24px', '0', '12px'),
  },
  heroBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    ...shorthands.padding('6px', '12px'),
    borderRadius: '999px',
    backgroundColor: 'rgba(117, 172, 242, 0.18)',
    color: '#dce9ff',
    fontSize: '14px',
    fontWeight: 600,
    letterSpacing: '0.02em',
  },
  heroTitle: {
    fontSize: 'clamp(2.75rem, 5vw, 3.75rem)',
    fontWeight: 700,
    margin: 0,
    color: '#f8fbff',
  },
  heroSubtitle: {
    marginTop: '12px',
    marginBottom: '32px',
    fontSize: '1.05rem',
    color: 'var(--colorNeutralForeground2)',
    maxWidth: '560px',
  },
  heroActions: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '16px',
  },
  heroVisualization: {
    background: 'radial-gradient(circle at 20% 20%, rgba(117,172,242,0.45), transparent 60%)',
    borderRadius: '32px',
    minHeight: '280px',
    position: 'relative',
    overflow: 'hidden',
    boxShadow: '0 25px 60px rgba(8, 14, 30, 0.55)',
  },
  orbit: {
    position: 'absolute',
    inset: '20px',
    borderRadius: '50%',
    border: '1px dashed rgba(117,172,242,0.45)',
  },
  core: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    borderRadius: '50%',
    width: '140px',
    height: '140px',
    background: 'linear-gradient(135deg, rgba(50,116,198,0.9), rgba(14,53,103,0.85))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#ffffff',
    fontWeight: 600,
    fontSize: '18px',
    boxShadow: '0 18px 36px rgba(18, 32, 56, 0.45)',
  },
  featureGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: '24px',
    marginTop: '56px',
  },
  featureIcon: {
    width: '48px',
    height: '48px',
    borderRadius: '14px',
    backgroundColor: 'rgba(117,172,242,0.16)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#9cc2f7',
    marginBottom: '16px',
  },
  trustBar: {
    marginTop: '72px',
    borderRadius: '24px',
    background: 'linear-gradient(135deg, rgba(14,53,103,0.9), rgba(22,66,118,0.85))',
    ...shorthands.padding('32px', '36px'),
    display: 'grid',
    gap: '24px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    boxShadow: '0 20px 45px rgba(6, 12, 25, 0.55)',
  },
  trustMetric: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
});

const ChatIcon = bundleIcon(ChatSparkle24Filled, ChatSparkle24Regular);
const GridIcon = bundleIcon(Grid24Filled, Grid24Regular);
const MapIcon = bundleIcon(Map24Filled, Map24Regular);
const TeamIcon = bundleIcon(PeopleTeam24Filled, PeopleTeam24Regular);
const ShieldIcon = bundleIcon(ShieldGlobe24Filled, ShieldGlobe24Regular);

export default function Home() {
  const styles = useStyles();

  return (
    <Layout>
      <Head>
        <title>Universal Knowledge Graph System</title>
      </Head>

      <section className={styles.hero}>
        <div>
          <span className={styles.heroBadge}>Microsoft-aligned enterprise knowledge fabric</span>
          <h1 className={styles.heroTitle}>Orchestrate compliant intelligence with UKG</h1>
          <p className={styles.heroSubtitle}>
            The Universal Knowledge Graph fuses regulatory controls, operational telemetry, and contextual expertise into a single
            trusted source of insight designed for enterprise-grade decision making.
          </p>

          <div className={styles.heroActions}>
            <Button
              icon={<ChatIcon />}
              variant="primary"
              size="lg"
              as={Link}
              href="/chat"
            >
              Launch conversational workspace
            </Button>
            <Button
              variant="outline"
              size="lg"
              as={Link}
              href="/knowledge-graph"
            >
              Explore the knowledge model
            </Button>
          </div>
        </div>

        <div className={styles.heroVisualization}>
          <div className={styles.orbit} />
          <div className={styles.core}>UKG Core</div>
        </div>
      </section>

      <section className={styles.featureGrid}>
        <Card>
          <Card.Body>
            <div className={styles.featureIcon}>
              <GridIcon fontSize={22} />
            </div>
            <Text fontSize="xl" fontWeight="semibold">
              13-axis knowledge framework
            </Text>
            <Text fontSize="md" color="muted">
              Harmonize organizational intelligence across pillars, regulatory domains, locations, and time to accelerate resilient decisions.
            </Text>
            <Button variant="subtle" as={Link} href="/pillars">
              Review the structure
            </Button>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <div className={styles.featureIcon}>
              <MapIcon fontSize={22} />
            </div>
            <Text fontSize="xl" fontWeight="semibold">
              Context-aware orchestration
            </Text>
            <Text fontSize="md" color="muted">
              Bring global and local perspectives together with spatial intelligence, expertise graphs, and compliance telemetry.
            </Text>
            <Button variant="subtle" as={Link} href="/locations">
              Navigate deployments
            </Button>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <div className={styles.featureIcon}>
              <TeamIcon fontSize={22} />
            </div>
            <Text fontSize="xl" fontWeight="semibold">
              Persona-driven reasoning
            </Text>
            <Text fontSize="md" color="muted">
              Activate knowledge, skill, role, and context experts that collaborate to deliver audit-ready recommendations.
            </Text>
            <Button variant="subtle" as={Link} href="/contextual">
              Meet the experts
            </Button>
          </Card.Body>
        </Card>
      </section>

      <section className={styles.trustBar}>
        <div className={styles.trustMetric}>
          <Text fontSize="sm" fontWeight="semibold" color="muted">
            Compliance posture
          </Text>
          <Text fontSize="2xl" fontWeight="bold">
            98.4% SOC 2 coverage
          </Text>
          <Text fontSize="sm" color="muted">
            Continuous controls mapped across trust service criteria, refreshed every 24 hours.
          </Text>
        </div>
        <div className={styles.trustMetric}>
          <Text fontSize="sm" fontWeight="semibold" color="muted">
            Knowledge resolution
          </Text>
          <Text fontSize="2xl" fontWeight="bold">
            2.7M graph relationships
          </Text>
          <Text fontSize="sm" color="muted">
            Unified schema spanning regulatory, operational, and contextual taxonomies.
          </Text>
        </div>
        <div className={styles.trustMetric}>
          <div className={styles.featureIcon}>
            <ShieldIcon fontSize={22} />
          </div>
          <Text fontSize="xl" fontWeight="semibold">
            Enterprise governance baked in
          </Text>
          <Text fontSize="sm" color="muted">
            Encryption, traceability, and policy inheritance aligned with Microsoft security baselines.
          </Text>
        </div>
      </section>
    </Layout>
  );
}
