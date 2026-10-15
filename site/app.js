(() => {
  const raceModes = [...document.querySelectorAll('.mode')];
  const runRace = document.querySelector('#run-race');
  const raceResult = document.querySelector('#race-result');
  const workers = [document.querySelector('#worker-a'), document.querySelector('#worker-b')];
  let raceMode = 'unsafe';
  let raceTimer = null;

  raceModes.forEach((button) => {
    button.addEventListener('click', () => {
      raceMode = button.dataset.mode;
      raceModes.forEach((candidate) => candidate.classList.toggle('active', candidate === button));
      workers.forEach((worker) => {
        worker.className = 'worker';
        worker.querySelector('span').textContent = 'READY';
      });
      raceResult.className = 'result-panel';
      raceResult.innerHTML = '<span class="result-kicker">OBSERVATION</span><strong>Mode changed. Run the synthetic race.</strong><p>No result is shown until you run the demonstration.</p>';
    });
  });

  runRace.addEventListener('click', () => {
    if (raceTimer) window.clearTimeout(raceTimer);
    workers.forEach((worker) => {
      worker.className = 'worker running';
      worker.querySelector('span').textContent = 'RACING →';
    });
    raceResult.className = 'result-panel';
    raceResult.innerHTML = '<span class="result-kicker">TRACE RUNNING</span><strong>Both workers received the same synthetic request.</strong><p>Resolving the selected boundary...</p>';

    raceTimer = window.setTimeout(() => {
      if (raceMode === 'unsafe') {
        workers.forEach((worker) => worker.querySelector('span').textContent = 'MUTATION ACCEPTED');
        raceResult.className = 'result-panel bad';
        raceResult.innerHTML = '<span class="result-kicker">SIMULATED FAILURE</span><strong>2 mutations accepted for 1 logical request.</strong><p>The unsafe visualization demonstrates the check-then-write race explored by Lab 01. See the repository tests for reproducible evidence.</p>';
      } else {
        workers[0].querySelector('span').textContent = 'MUTATION ACCEPTED';
        workers[1].className = 'worker blocked';
        workers[1].querySelector('span').textContent = 'DUPLICATE BLOCKED';
        raceResult.className = 'result-panel good';
        raceResult.innerHTML = '<span class="result-kicker">SIMULATED INVARIANT</span><strong>1 mutation accepted. Duplicate work is contained.</strong><p>The visualization mirrors the idempotency invariant explored and tested in Lab 01; it is not a live production transaction.</p>';
      }
    }, 800);
  });

  const catalog = [
    { id: 'fixture-a', name: 'Northstar Sensor', environment: 'indoor', power: 'wired' },
    { id: 'fixture-b', name: 'Trailhead Sensor', environment: 'outdoor', power: 'battery' },
    { id: 'fixture-c', name: 'Workshop Sensor', environment: 'indoor', power: 'battery' }
  ];
  const catalogEl = document.querySelector('#catalog');
  const environment = document.querySelector('#environment');
  const inject = document.querySelector('#inject');
  const runBoundary = document.querySelector('#run-boundary');
  const boundaryResult = document.querySelector('#boundary-result');

  function renderCatalog(required) {
    catalogEl.innerHTML = catalog.map((item) => {
      const eligible = item.environment === required;
      return `<div class="item ${eligible ? 'eligible' : 'rejected'}"><strong>${item.name}</strong><span>${item.id} // ${item.environment} // ${item.power}</span><span>${eligible ? '✓ ELIGIBLE' : '× FILTERED BEFORE RANKING'}</span></div>`;
    }).join('');
  }

  renderCatalog(environment.value);
  environment.addEventListener('change', () => {
    renderCatalog(environment.value);
    boundaryResult.className = 'result-panel';
    boundaryResult.innerHTML = '<span class="result-kicker">BOUNDARY TRACE</span><strong>Constraint changed.</strong><p>Run the boundary to trace the synthetic recommendation.</p>';
  });

  runBoundary.addEventListener('click', () => {
    const required = environment.value;
    const eligible = catalog.filter((item) => item.environment === required);
    renderCatalog(required);
    if (inject.checked) {
      const ineligible = catalog.find((item) => item.environment !== required);
      boundaryResult.className = 'result-panel good';
      boundaryResult.innerHTML = `<span class="result-kicker">REJECTED AT DETERMINISTIC BOUNDARY</span><strong>${ineligible.name} cannot re-enter the eligible set.</strong><p>Required environment: ${required}. The injected item is ${ineligible.environment}, so the post-ranking validation rejects it even though it exists in the authoritative synthetic catalog.</p>`;
    } else {
      boundaryResult.className = 'result-panel good';
      boundaryResult.innerHTML = `<span class="result-kicker">BOUNDARY HELD</span><strong>${eligible.length} eligible candidate${eligible.length === 1 ? '' : 's'} reached the flexible stage.</strong><p>Only catalog-backed items satisfying the hard ${required} constraint are available for ranking and factual validation.</p>`;
    }
  });
})();
