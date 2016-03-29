sub getHS
{
	my $ms; # result as return value
	my $rest;
	my ($parameter) = @_;
	if ($parameter == 0)
	{
		return ("A");
	}
	if ($parameter < 200000)
	{
		$ms = $parameter/10-10000;
		$ms = 'P'.$ms;
	}
	
	if ($parameter > 200000 and $parameter < 300000)
	{
		if ($parameter % 10 > 0)
		{
			$rest = int($parameter % 10);
			$ms = ($parameter-$rest)/10-20000;
			$ms = '0'.$ms.'s';
			if($rest > 1)
			{
				$ms = $ms.$rest;
			}
		} else {
			$ms = $parameter/10-20000;
			$ms = '0'.$ms;
		}
	}
	
	if ($parameter > 300000)
	{
		if ($parameter % 10 > 0)
		{
			$rest = int($parameter % 10);
			$ms = ($parameter-$rest)/10-30000;
			$ms = $ms.'s';
			if($rest > 1)
			{
				$ms = $ms.$rest;
			}
		} else {
			$ms = $parameter/10-30000;
		}
	}

	if ($parameter > 400000)
	{
		if ($parameter % 10 > 0)
		{
			$rest = int($parameter % 10);
			$ms = ($parameter-$rest)/10-40000;
			$ms = 'L'.$ms.'s';
			if($rest > 1)
			{
				$ms = $ms.$rest;
			}
		} else {
			$ms = $parameter/10-40000;
			$ms = 'L'.$ms;
		}
	}
	return $ms;
}	
# Vorlage von Klaus Wachtel, Änderungen von Volker Krüger
1;