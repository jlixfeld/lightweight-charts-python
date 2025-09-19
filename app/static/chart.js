(() => {
  const state = window.__LWC_STATE__ || {};
  const chartContainer = document.getElementById('chart');
  const emptyNotice = document.getElementById('empty');
  const errorBanner = document.getElementById('error-banner');
  const symbolSelect = document.getElementById('symbol-select');
  const timeframeSelect = document.getElementById('timeframe-select');
  const timeframeWrapper = document.getElementById('timeframe-wrapper');
  const patternToggle = document.getElementById('pattern-toggle');

  if (!chartContainer) {
    console.error('Chart container not found');
    return;
  }

  // Bar Pattern Detection System
  class BarPatterns {
    static PATTERNS = {
      INSIDE_BAR: 'inside_bar',
      OUTSIDE_BAR: 'outside_bar',
    };

    static detectPattern(current, previous) {
      if (!previous) return null;

      // Inside Bar: Current high/low within previous high/low
      if (current.high <= previous.high && current.low >= previous.low) {
        return this.PATTERNS.INSIDE_BAR;
      }

      // Outside Bar: Current high/low exceed previous high/low
      if (current.high > previous.high && current.low < previous.low) {
        return this.PATTERNS.OUTSIDE_BAR;
      }

      return null;
    }

    static applyPatternColors(candleData) {
      let patternsFound = { inside: 0, outside: 0 };

      const result = candleData.map((candle, index) => {
        if (index === 0) return candle;

        const current = candle;
        const previous = candleData[index - 1];
        const pattern = this.detectPattern(current, previous);

        if (pattern) {
          console.log(`Pattern detected at index ${index}:`, pattern);

          if (pattern === this.PATTERNS.INSIDE_BAR) {
            patternsFound.inside++;
            const isBullish = current.close >= current.open;
            return {
              ...current,
              color: 'white',
              wickColor: isBullish ? '#26a69a' : '#ef5350'
            };
          }

          if (pattern === this.PATTERNS.OUTSIDE_BAR) {
            patternsFound.outside++;
            const isBullish = current.close >= current.open;
            return {
              ...current,
              color: 'yellow',
              wickColor: isBullish ? '#26a69a' : '#ef5350'
            };
          }
        }

        return candle;
      });

      console.log(`Bar patterns detected: ${patternsFound.inside} inside bars, ${patternsFound.outside} outside bars`);
      return result;
    }
  }

  // Handle initial state errors
  if (state.error) {
    errorBanner.textContent = state.error;
    errorBanner.style.display = 'block';
  }

  if (!state.symbols || state.symbols.length === 0) {
    emptyNotice.style.display = 'block';
    emptyNotice.textContent = 'No symbols available. Ensure the dataset is populated.';
    return;
  }

  // Populate dropdowns
  state.symbols.forEach((symbol) => {
    const option = document.createElement('option');
    option.value = symbol;
    option.textContent = symbol;
    symbolSelect.appendChild(option);
  });
  symbolSelect.value = state.activeSymbol || state.symbols[0];

  if (!state.timeframes || state.timeframes.length === 0) {
    timeframeWrapper.style.display = 'none';
  } else {
    state.timeframes.forEach((tf) => {
      const option = document.createElement('option');
      option.value = tf;
      option.textContent = tf;
      timeframeSelect.appendChild(option);
    });
    timeframeSelect.value = state.activeTimeframe || state.timeframes[0];
  }

  let currentSymbol = symbolSelect.value;
  let currentTimeframe = state.timeframes && state.timeframes.length
    ? timeframeSelect.value || null
    : null;

  // Create chart using v4.2.0 API
  const chart = LightweightCharts.createChart(chartContainer, {
    layout: { background: { color: '#11161c' }, textColor: '#d8dee9' },
    width: chartContainer.clientWidth,
    height: chartContainer.clientHeight,
    grid: {
      horzLines: { color: '#1f2933' },
      vertLines: { color: '#1f2933' },
    },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderVisible: false },
    timeScale: { borderVisible: false },
  });

  const candleSeries = chart.addCandlestickSeries({
    upColor: '#26a69a', downColor: '#ef5350',
    borderUpColor: '#26a69a', borderDownColor: '#ef5350',
    wickUpColor: '#26a69a', wickDownColor: '#ef5350',
  });

  window.addEventListener('resize', () => {
    chart.applyOptions({
      width: chartContainer.clientWidth,
      height: chartContainer.clientHeight,
    });
  });

  symbolSelect.addEventListener('change', () => {
    currentSymbol = symbolSelect.value;
    loadData();
  });

  if (state.timeframes && state.timeframes.length) {
    timeframeSelect.addEventListener('change', () => {
      currentTimeframe = timeframeSelect.value;
      loadData();
    });
  }

  patternToggle.addEventListener('change', () => {
    loadData();
  });

  async function loadData() {
    try {
      console.log('Loading data for:', currentSymbol, currentTimeframe);

      const params = new URLSearchParams({ symbol: currentSymbol });
      if (currentTimeframe) {
        params.append('timeframe', currentTimeframe);
      }
      params.append('limit', state.limit || 500);

      const response = await fetch(`/ohlc?${params.toString()}`);
      if (!response.ok) {
        const message = await response.text();
        console.error('Failed to load data:', message);
        errorBanner.textContent = `Failed to load data: ${message}`;
        errorBanner.style.display = 'block';
        return;
      }

      const rows = await response.json();
      console.log('Received data rows:', rows.length);

      if (!rows.length) {
        emptyNotice.style.display = 'block';
        candleSeries.setData([]);
        return;
      }

      emptyNotice.style.display = 'none';
      errorBanner.style.display = 'none';

      const candleData = rows.map((row) => {
        const time = Math.floor(new Date(row.time).getTime() / 1000);
        return {
          time,
          open: parseFloat(row.open),
          high: parseFloat(row.high),
          low: parseFloat(row.low),
          close: parseFloat(row.close),
        };
      });

      console.log('Converted candlestick data:', candleData.length, 'candles');

      const finalCandleData = patternToggle.checked
        ? BarPatterns.applyPatternColors(candleData)
        : candleData;

      console.log('Setting data to chart...');
      candleSeries.setData(finalCandleData);

      chart.timeScale().fitContent();

      console.log('Data loading completed successfully');

    } catch (error) {
      console.error('Error loading data:', error);
      errorBanner.textContent = `Error loading data: ${error.message}`;
      errorBanner.style.display = 'block';
    }
  }

  console.log('Initializing chart with state:', state);
  loadData();
})();